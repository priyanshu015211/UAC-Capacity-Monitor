"""
data_processing.py
==================
UAC Healthcare System Capacity Analytics Pipeline
Step 1-3: Data Ingestion, Validation, and Feature Engineering

Author: UAC Analytics Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# COLUMN ALIASES  (map raw CSV headers → short internal names)
# ─────────────────────────────────────────────────────────────────────────────
COLUMN_MAP = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "cbp_apprehended",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "cbp_transfers",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "hhs_discharged",
}

NUMERIC_COLS = ["cbp_apprehended", "cbp_custody", "cbp_transfers", "hhs_care", "hhs_discharged"]


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — DATA INGESTION & PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def load_and_preprocess(filepath: str) -> tuple[pd.DataFrame, dict]:
    """
    Load CSV, rename columns, parse dates, sort, reindex to a continuous daily
    date range, forward-fill gaps and flag them, remove duplicates.

    Returns
    -------
    df   : cleaned DataFrame ready for validation
    meta : dict with preprocessing stats
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    # ── 1a. Raw load ────────────────────────────────────────────────────────
    raw = pd.read_csv(filepath)

    # Drop rows where ALL fields are NaN (the trailing empty rows in CSV)
    raw.dropna(how="all", inplace=True)

    # ── 1b. Rename columns ──────────────────────────────────────────────────
    # Handle asterisk variant in header
    raw.columns = [c.strip() for c in raw.columns]
    rename_map = {}
    for orig_col, short_col in COLUMN_MAP.items():
        for raw_col in raw.columns:
            if orig_col.replace("*", "").strip() in raw_col.replace("*", "").strip():
                rename_map[raw_col] = short_col
    raw.rename(columns=rename_map, inplace=True)

    # ── 1c. Parse dates ─────────────────────────────────────────────────────
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    raw.dropna(subset=["date"], inplace=True)  # Drop rows with unparseable dates

    # ── 1d. Remove duplicate records ────────────────────────────────────────
    n_before = len(raw)
    raw.drop_duplicates(subset=["date"], keep="first", inplace=True)
    n_duplicates = n_before - len(raw)

    # ── 1e. Sort chronologically ────────────────────────────────────────────
    raw.sort_values("date", inplace=True)
    raw.reset_index(drop=True, inplace=True)

    # ── 1f. Strip commas from numeric columns and cast ──────────────────────
    for col in NUMERIC_COLS:
        if col in raw.columns:
            raw[col] = (
                raw[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            raw[col] = pd.to_numeric(raw[col], errors="coerce")

    # ── 1g. Reindex to continuous daily date range ──────────────────────────
    full_idx = pd.date_range(start=raw["date"].min(), end=raw["date"].max(), freq="D")
    raw = raw.set_index("date").reindex(full_idx)
    raw.index.name = "date"
    raw.reset_index(inplace=True)

    # ── 1h. Forward-fill missing values & flag them ──────────────────────────
    ffill_mask = raw[NUMERIC_COLS].isna()
    n_missing_before = ffill_mask.sum().sum()

    raw[NUMERIC_COLS] = raw[NUMERIC_COLS].ffill()

    # Add boolean flag column for each imputed row
    raw["is_imputed"] = ffill_mask.any(axis=1)

    meta = {
        "n_raw_rows": n_before,
        "n_duplicates_removed": n_duplicates,
        "n_missing_cells_imputed": int(n_missing_before),
        "n_imputed_rows": int(raw["is_imputed"].sum()),
        "date_range_start": raw["date"].min(),
        "date_range_end": raw["date"].max(),
        "total_days": len(raw),
    }

    return raw, meta


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Apply strict business rules and flag anomalies.

    Rules
    -----
    1. Transfers ≤ CBP custody
    2. Discharges ≤ HHS care
    3. No negative values in any numeric column

    Returns
    -------
    df_clean   : DataFrame with anomaly flag column added
    df_anomaly : Rows that violate at least one rule
    report     : Summary dict
    """
    df = df.copy()
    df["anomaly_flags"] = ""

    def _flag(mask: pd.Series, label: str):
        df.loc[mask, "anomaly_flags"] = (
            df.loc[mask, "anomaly_flags"] + label + "; "
        )

    # Rule 1: Transfers cannot exceed CBP custody on same day
    r1 = df["cbp_transfers"] > df["cbp_custody"]
    _flag(r1, "TRANSFER>CUSTODY")

    # Rule 2: Discharges cannot exceed HHS care population
    r2 = df["hhs_discharged"] > df["hhs_care"]
    _flag(r2, "DISCHARGE>HSSCARE")

    # Rule 3: No negative values
    for col in NUMERIC_COLS:
        neg_mask = df[col] < 0
        _flag(neg_mask, f"NEG:{col.upper()}")

    df["has_anomaly"] = df["anomaly_flags"].str.strip() != ""
    df_anomaly = df[df["has_anomaly"]].copy()

    report = {
        "total_records": len(df),
        "anomaly_count": int(df["has_anomaly"].sum()),
        "anomaly_pct": round(df["has_anomaly"].mean() * 100, 2),
        "rule_transfer_exceeds_custody": int(r1.sum()),
        "rule_discharge_exceeds_care": int(r2.sum()),
        "rule_negative_values": int((df["anomaly_flags"].str.contains("NEG:")).sum()),
        "missing_imputed_rows": int(df["is_imputed"].sum()),
    }

    return df, df_anomaly, report


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create all derived metrics and rolling statistics.

    Derived Metrics
    ---------------
    total_system_load   = cbp_custody + hhs_care
    net_daily_intake    = cbp_transfers - hhs_discharged
    care_load_growth    = day-over-day % change in total_system_load
    backlog_indicator   = rolling cumulative sum of positive net intakes

    Rolling Metrics
    ---------------
    ma_7   : 7-day moving average of total_system_load
    ma_14  : 14-day moving average of total_system_load
    vol_7  : 7-day rolling std-dev of total_system_load (volatility proxy)
    """
    df = df.copy()

    # ── Core derived metrics ─────────────────────────────────────────────────
    df["total_system_load"] = df["cbp_custody"] + df["hhs_care"]
    df["net_daily_intake"]  = df["cbp_transfers"] - df["hhs_discharged"]

    # Care load growth rate (percentage change, fill first NaN with 0)
    df["care_load_growth"] = (
        df["total_system_load"].pct_change() * 100
    ).fillna(0)

    # Backlog: cumulative sum of positive net intakes only
    positive_intake = df["net_daily_intake"].clip(lower=0)
    df["backlog_indicator"] = positive_intake.cumsum()

    # ── Rolling statistics ───────────────────────────────────────────────────
    df["ma_7"]  = df["total_system_load"].rolling(window=7,  min_periods=1).mean()
    df["ma_14"] = df["total_system_load"].rolling(window=14, min_periods=1).mean()
    df["vol_7"] = df["total_system_load"].rolling(window=7,  min_periods=2).std().fillna(0)

    # ── Additional utility columns ───────────────────────────────────────────
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week"]  = df["date"].dt.isocalendar().week.astype(int)
    df["quarter"] = df["date"].dt.quarter

    return df


# ═══════════════════════════════════════════════════════════════════════════
# RESAMPLING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

AGG_MAP = {
    "cbp_apprehended":  "sum",
    "cbp_custody":      "mean",
    "cbp_transfers":    "sum",
    "hhs_care":         "mean",
    "hhs_discharged":   "sum",
    "total_system_load":"mean",
    "net_daily_intake": "sum",
    "care_load_growth": "mean",
    "backlog_indicator":"last",
    "ma_7":             "last",
    "ma_14":            "last",
    "vol_7":            "mean",
}

def resample_data(df: pd.DataFrame, granularity: str = "D") -> pd.DataFrame:
    """
    Resample processed DataFrame to a given time granularity.

    Parameters
    ----------
    granularity : 'D' (daily), 'W' (weekly), 'ME' or 'M' (monthly)
    """
    # Normalise monthly alias across pandas versions
    # pandas < 2.2 uses "M"; pandas >= 2.2 uses "ME"
    if granularity in ("ME", "M"):
        _pd_ver = tuple(int(x) for x in pd.__version__.split(".")[:2])
        granularity = "ME" if _pd_ver >= (2, 2) else "M"

    df_indexed = df.set_index("date")
    cols_to_resample = [c for c in AGG_MAP if c in df_indexed.columns]
    agg = {c: AGG_MAP[c] for c in cols_to_resample}
    resampled = df_indexed[cols_to_resample].resample(granularity).agg(agg)
    resampled.reset_index(inplace=True)
    return resampled


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE: full pipeline in one call
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(filepath: str):
    """
    Execute Steps 1-3 end-to-end and return all artefacts.

    Returns
    -------
    df_final   : fully processed & featured DataFrame
    df_anomaly : anomaly records
    meta       : ingestion metadata dict
    val_report : validation summary dict
    """
    df, meta        = load_and_preprocess(filepath)
    df, df_anomaly, val_report = validate_data(df)
    df_final        = engineer_features(df)
    return df_final, df_anomaly, meta, val_report


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "HHS_Unaccompanied_Alien_Children_Program__1_.csv"
    df, anom, meta, rep = run_pipeline(path)
    print("=== Ingestion Metadata ===")
    for k, v in meta.items():
        print(f"  {k}: {v}")
    print("\n=== Validation Report ===")
    for k, v in rep.items():
        print(f"  {k}: {v}")
    print(f"\nProcessed DataFrame shape: {df.shape}")
    print(df[["date","total_system_load","net_daily_intake","backlog_indicator"]].tail())
