from __future__ import annotations

from typing import Any

import pandas as pd


def available(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns


def kpis(df: pd.DataFrame) -> dict[str, Any]:
    fraud = df[df["_is_fraud"]] if "_is_fraud" in df else df.iloc[0:0]
    amount = pd.to_numeric(fraud.get("Amount", pd.Series(dtype=float)), errors="coerce")
    risk = pd.to_numeric(df.get("Risk_Score", pd.Series(dtype=float)), errors="coerce")
    total_amount = amount.sum(min_count=1)
    return {
        "transactions": int(len(df)), "fraud_count": int(len(fraud)),
        "fraud_pct": (100 * len(fraud) / len(df)) if len(df) else 0.0,
        "fraud_labelled_amount": float(total_amount) if pd.notna(total_amount) else 0.0,
        "avg_risk": float(risk.mean()) if risk.notna().any() else None,
    }


def grouped_fraud(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df:
        return pd.DataFrame(columns=[column, "fraud_count", "fraud_amount"])
    fraud = df[df["_is_fraud"]].copy()
    if fraud.empty:
        return pd.DataFrame(columns=[column, "fraud_count", "fraud_amount"])
    fraud[column] = fraud[column].astype("string").fillna("Unknown")
    amount = pd.to_numeric(fraud["Amount"], errors="coerce") if "Amount" in fraud else pd.Series(float("nan"), index=fraud.index)
    fraud["_amount"] = amount
    return fraud.groupby(column, dropna=False).agg(fraud_count=("_is_fraud", "size"), fraud_amount=("_amount", lambda x: x.sum(min_count=1))).reset_index().sort_values(["fraud_count", column], ascending=[False, True])


def filter_transactions(df: pd.DataFrame, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    result = df.copy()
    filters = filters or {}
    for key in ("City", "Payment_Method", "Merchant_Category", "Transaction_Type", "Device_Type", "Bank_Name", "Age_Group"):
        value = filters.get(key)
        if value and value != "All" and key in result:
            result = result[result[key].fillna("Unknown").isin(value if isinstance(value, list) else [value])]
    status = filters.get("Fraud_Status")
    if status and status != "All":
        result = result[result["_is_fraud"] == (str(status).casefold() == "fraud")]
    query = str(filters.get("search", "")).strip().casefold()
    if query and "Transaction_ID" in result:
        result = result[result["Transaction_ID"].astype("string").str.casefold().str.contains(query, regex=False, na=False)]
    for col, bound in (("Amount", filters.get("amount_range")), ("Risk_Score", filters.get("risk_range"))):
        if bound and col in result:
            vals = pd.to_numeric(result[col], errors="coerce")
            result = result[vals.between(bound[0], bound[1])]
    dates = filters.get("date_range")
    if dates and "Transaction_Date" in result:
        d = pd.to_datetime(result["Transaction_Date"], errors="coerce")
        start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1])
        result = result[d.between(start, end + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))]
    return result


def high_value_fraud(df: pd.DataFrame, threshold: float = 10000, limit: int = 100) -> pd.DataFrame:
    if "Amount" not in df:
        return df.iloc[0:0]
    amount = pd.to_numeric(df["Amount"], errors="coerce")
    return df[df["_is_fraud"] & amount.gt(threshold)].sort_values("Amount", ascending=False).head(limit)


def deterministic_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    """Compact, privacy-conscious facts for AI prompts and report generation."""
    facts: dict[str, Any] = {"kpis": kpis(df)}
    for col in ("Payment_Method", "Merchant_Category", "City"):
        if col in df:
            facts[col] = grouped_fraud(df, col).head(8).to_dict(orient="records")
    if "Risk_Score" in df:
        fraud_risk = pd.to_numeric(df.loc[df["_is_fraud"], "Risk_Score"], errors="coerce")
        facts["fraud_risk_summary"] = {"mean": round(float(fraud_risk.mean()), 2) if fraud_risk.notna().any() else None, "median": round(float(fraud_risk.median()), 2) if fraud_risk.notna().any() else None}
    facts["high_value_fraud_count_over_10000"] = len(high_value_fraud(df, 10000)) if "Amount" in df else None
    facts["definitions"] = "Fraud means Fraud_Status exactly equals Fraud (case-insensitive). Amount sums are amounts on labelled records, not confirmed losses. Exact duplicate rows are removed once at load time."
    return facts
