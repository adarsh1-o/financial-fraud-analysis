from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"Transaction_ID", "Fraud_Status"}
DATA_FILE = Path(__file__).resolve().parents[1] / "financial_fraud_dataset_10000.csv"


def load_transactions(path: str | Path = DATA_FILE) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load source rows, remove only exact duplicate records for analysis, and normalize types."""
    source = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(source.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    raw_count = len(source)
    exact_dupes = int(source.duplicated().sum())
    df = source.drop_duplicates().copy()
    if "Amount" in df:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df.loc[df["Amount"] < 0, "Amount"] = pd.NA
    if "Risk_Score" in df:
        df["Risk_Score"] = pd.to_numeric(df["Risk_Score"], errors="coerce")
    if "Transaction_Date" in df:
        df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")
    string_columns = [col for col in df.columns if df[col].dtype == object or isinstance(df[col].dtype, pd.StringDtype)]
    for col in string_columns:
        df[col] = df[col].replace(r"^\s*$", pd.NA, regex=True)
    labels = df["Fraud_Status"].astype("string").str.strip().str.casefold()
    df["_is_fraud"] = labels.eq("fraud").fillna(False)
    metadata = {"source_rows": raw_count, "exact_duplicates_removed": exact_dupes, "analysis_rows": len(df)}
    return df, metadata
