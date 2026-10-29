from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from .analytics import deterministic_snapshot, grouped_fraud, high_value_fraud
from .config import gemini_api_key, gemini_model

MODEL = gemini_model()


def calculate_answer(question: str, df) -> dict[str, Any]:
    q = question.strip().casefold()
    if not q:
        return {"supported": False, "message": "Enter a question about the supplied dataset."}
    if any(x in q for x in ("payment", "method")):
        return {"supported": True, "operation": "fraud by payment method", "results": grouped_fraud(df, "Payment_Method").head(8).to_dict("records")}
    if any(x in q for x in ("merchant", "category")):
        return {"supported": True, "operation": "fraud by merchant category", "results": grouped_fraud(df, "Merchant_Category").head(8).to_dict("records")}
    if "city" in q or "cities" in q or "geograph" in q:
        return {"supported": True, "operation": "fraud by city", "results": grouped_fraud(df, "City").head(5).to_dict("records")}
    if any(x in q for x in ("above", "over", "greater than", "high-value", "high value")) and "fraud" in q:
        match = re.search(r"(?:above|over|greater than)\s*\$?\s*([\d,]+(?:\.\d+)?)", q)
        threshold = float(match.group(1).replace(",", "")) if match else 10000.0
        rows = high_value_fraud(df, threshold)
        return {"supported": True, "operation": "amount threshold", "threshold": threshold, "count": len(rows), "results": rows[[c for c in ("Transaction_ID", "Amount", "City", "Payment_Method", "Merchant_Category") if c in rows]].head(10).to_dict("records")}
    if any(x in q for x in ("summar", "important finding", "pattern", "investigat", "compare", "how many", "fraud percentage", "fraud rate")):
        return {"supported": True, "operation": "dataset summary", "results": deterministic_snapshot(df)}
    return {"supported": False, "message": "I can answer fraud counts and labelled amounts by payment method, merchant category, or city; high-value fraud counts; and a dataset summary."}


@lru_cache(maxsize=2)
def _cached_client(api_key: str):
    from google import genai
    from google.genai import types

    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=15000))


def get_gemini_client(api_key: str | None = None):
    key = api_key or gemini_api_key()
    if not key:
        raise ValueError("Gemini API key missing")
    return _cached_client(key)


def classify_api_error(exc: Exception) -> tuple[str, str]:
    """Classify SDK failures without returning exception text that could contain credentials."""
    code = getattr(exc, "code", None)
    message = str(getattr(exc, "message", exc)).casefold()
    status = str(getattr(exc, "status", "")).casefold()
    error_type = type(exc).__name__.casefold()
    if code == 429 or "resourceexhausted" in error_type or "429" in message or "resource_exhausted" in message or "quota" in message or "rate limit" in message:
        return "quota_exceeded", "Gemini quota or rate limit reached. Check your API quota and try again later."
    if (code == 404 or "notfound" in error_type) or "model not found" in message or "unsupported model" in message or ("model" in message and "not found" in message):
        return "unsupported_model", f"The configured Gemini model ({MODEL}) is unavailable to this API key. Check GEMINI_MODEL."
    if code in (401, 403) or "permissiondenied" in error_type or "unauthenticated" in error_type or "api_key_invalid" in message or "invalid api key" in message or "api key not valid" in message or "unauthenticated" in status:
        return "authentication_failed", "Gemini denied access. Verify the key is active and authorized for the Gemini Developer API; check its API restrictions and project permissions."
    if isinstance(exc, (TimeoutError,)) or "timeout" in message or "timed out" in message:
        return "temporarily_unavailable", "Gemini did not respond before the timeout. Try again shortly."
    return "temporarily_unavailable", "Gemini is temporarily unavailable. Check network access and try again."


def test_gemini_connection(api_key: str | None = None) -> dict[str, str]:
    key = api_key or gemini_api_key()
    if not key:
        return {"status": "missing_key", "message": "Gemini API key missing. Add GEMINI_API_KEY to the local .env file."}
    try:
        response = get_gemini_client(key).interactions.create(
            model=MODEL,
            input="Reply with the single word READY.",
            store=False,
        )
        output_text = getattr(response, "output_text", None)
        if not output_text or not output_text.strip():
            return {"status": "invalid_response", "message": "Gemini returned an empty response. Verify the model and try again."}
        return {"status": "verified", "message": f"Gemini connection verified with {MODEL}."}
    except Exception as exc:
        status, message = classify_api_error(exc)
        return {"status": status, "message": message}


def explain(question: str, facts: dict[str, Any], api_key: str | None = None, client: Any = None) -> str:
    key = api_key or gemini_api_key()
    if not key and client is None:
        return "Gemini API key missing. The deterministic results are shown above; add GEMINI_API_KEY to the local .env file to enable AI explanations."
    try:
        client = client or get_gemini_client(key)
        payload = json.dumps(facts, default=str, ensure_ascii=False)
        prompt = (
            "Explain patterns in these calculated results in concise plain language. Do not write numeric figures; refer readers to the deterministic results shown alongside. "
            "Distinguish observed associations from causes. Amounts are sums on fraud-labelled records, not confirmed losses. "
            "State uncertainty and suggest verification by an analyst. If the results do not support the question, say so.\n"
            f"Question: {question[:500]}\nCalculated results: {payload[:12000]}"
        )
        response = client.interactions.create(model=MODEL, input=prompt, store=False)
        answer = getattr(response, "output_text", None)
        if not answer or not answer.strip():
            return "Gemini returned an empty response. The calculated results are shown above."
        if re.search(r"\d", answer):
            return "The generated explanation included numeric figures, so it was omitted. Review the deterministic results shown above."
        return answer.strip()
    except Exception as exc:
        _, message = classify_api_error(exc)
        return f"{message} The deterministic results are still available above."


def answer_question(question: str, df, api_key: str | None = None, client: Any = None) -> dict[str, Any]:
    calculated = calculate_answer(question, df)
    if not calculated.get("supported"):
        return {**calculated, "explanation": calculated["message"], "ai_status": "not_required"}
    explanation = explain(question, calculated, api_key, client)
    if "connection verified" in explanation.casefold():
        status = "verified"
    elif "api key missing" in explanation.casefold():
        status = "missing_key"
    elif "quota" in explanation.casefold() or "rate limit" in explanation.casefold():
        status = "quota_exceeded"
    elif "rejected the api key" in explanation.casefold() or "denied access" in explanation.casefold():
        status = "authentication_failed"
    elif "configured gemini model" in explanation.casefold():
        status = "unsupported_model"
    elif "temporarily unavailable" in explanation.casefold() or "timeout" in explanation.casefold():
        status = "temporarily_unavailable"
    else:
        status = "available"
    return {**calculated, "explanation": explanation, "ai_status": status}
