from __future__ import annotations

from datetime import datetime

from .analytics import deterministic_snapshot
from .ai_assistant import explain


def build_report(df, metadata: dict, api_key: str | None = None, client=None) -> str:
    facts = deterministic_snapshot(df)
    interpretation = explain("Summarize findings and identify patterns that deserve analyst follow-up.", facts, api_key, client)
    k = facts["kpis"]
    lines = ["# Financial Fraud Intelligence Report", f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}", "", "## 1. Executive Summary", interpretation,
             "", "## 2. Dataset Overview", f"- Source rows: {metadata.get('source_rows', len(df)):,}", f"- Exact duplicate rows excluded from analysis: {metadata.get('exact_duplicates_removed', 0):,}", f"- Analyzed rows: {len(df):,}",
             "", "## 3. Key Fraud Metrics", f"- Fraud-labelled records: {k['fraud_count']:,} of {k['transactions']:,} ({k['fraud_pct']:.2f}%).", f"- Amount on fraud-labelled records: {k['fraud_labelled_amount']:,.2f} (not confirmed loss)."]
    if k["avg_risk"] is not None:
        lines.append(f"- Mean risk score across analyzed records: {k['avg_risk']:.2f}.")
    for i, (title, key) in enumerate((("Payment Method Analysis", "Payment_Method"), ("Merchant Category Analysis", "Merchant_Category"), ("Geographic Patterns", "City")), start=4):
        lines.extend(["", f"## {i}. {title}"])
        rows = facts.get(key, [])
        if rows:
            lines.append("| Group | Fraud-labelled count | Labelled amount |")
            lines.append("|---|---:|---:|")
            for row in rows:
                amount = row.get("fraud_amount")
                amount_text = f"{amount:,.2f}" if amount is not None else "Unavailable"
                lines.append(f"| {row.get(key, 'Unknown')} | {row.get('fraud_count', 0):,} | {amount_text} |")
        else:
            lines.append("Not available in this dataset.")
    lines.extend(["", "## 7. High-Value Fraud-Labelled Transactions", f"Records above 10,000: {facts['high_value_fraud_count_over_10000'] if facts['high_value_fraud_count_over_10000'] is not None else 'Unavailable'}.",
                  "", "## 8. Potential Patterns Requiring Investigation", interpretation,
                  "", "## 9. Recommended Analytical Follow-Ups", "- Validate patterns against independently confirmed case outcomes.", "- Compare rates using suitable exposure denominators, not counts alone.", "- Review data quality and the influence of missing amounts and duplicate records.",
                  "", "## 10. Limitations", "- Fraud status is the dataset label; it does not establish adjudicated loss.", "- Amounts are summed from labelled rows and are not confirmed losses.", "- This is descriptive analysis and does not implement or evaluate predictive fraud detection.", "- AI narrative requires analyst verification; deterministic figures above are calculated from the data."])
    return "\n".join(lines)
