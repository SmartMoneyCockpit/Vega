# pages/04_Screener_Text.py
import os
import glob
import math
import pandas as pd
import streamlit as st
from typing import Tuple, Optional

st.set_page_config(page_title="Screener — Text v1.4", layout="wide")
st.title("Screener — Text v1.4")

# -----------------------------
# String safety + ticker parser
# -----------------------------
def _safe_str(x) -> str:
    """Return a trimmed string for any value; None/NaN -> ''."""
    if isinstance(x, str):
        return x.strip()
    if x is None:
        return ""
    try:
        if isinstance(x, float) and math.isnan(x):
            return ""
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def resolve_ticker(row: pd.Series) -> str:
    """
    Safely pick a ticker-like value from the row.
    Preference order tries common column names; then parses 'name' like
    'Acme Corp (ACME)' or 'ACME - Acme Corp'.
    """
    candidates = ("ticker", "symbol", "Ticker", "Symbol", "tv", "tradingview")
    for c in candidates:
        if c in row:
            s = _safe_str(row[c])
            if s:
                return s.upper()

    name = _safe_str(row.get("name", ""))
    # Parse NAME (TICKER)
    if "(" in name and ")" in name:
        inside = name.split("(")[-1].split(")")[0].strip()
        if inside:
            return inside.upper()
    # Parse TICKER - Company Name
    if " - " in name:
        left = name.split(" - ", 1)[0].strip()
        if left and all(ch.isupper() or ch == "." or ch.isdigit() for ch in left):
            return left.upper()
    return ""

# -----------------------------
# File discovery + loading
# -----------------------------
def _find_latest_file() -> Optional[str]:
    patterns = [
        "data/snapshots/**/*screener*.csv",
        "data/**/*screener*.csv",
        "reports/**/*screener*.csv",
        "output/**/*screener*.csv",
        "**/*screener*.csv",
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p, recursive=True))
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]

def _load_csv(path: str) -> pd.DataFrame:
    """
    Load CSV robustly for mixed types.
    - keep_default_na=False so empty cells stay empty strings (not NaN)
    - na_filter=True so truly blank stays '' and we can still detect NA if present
    """
    try:
        df = pd.read_csv(
            path,
            keep_default_na=False,  # don't convert "" -> NaN
            na_filter=True,         # but still recognize actual NA tokens if any
            low_memory=False
        )
    except Exception:
        # Fallback: let pandas infer normally
        df = pd.read_csv(path)
    return df

# -----------------------------
# Main
# -----------------------------
latest = _find_latest_file()
if not latest:
    st.info("No screener CSV found yet. Once the workflow drops a screener CSV, this page will render it.")
    st.stop()

df = _load_csv(latest)

if df.empty:
    st.info(f"Screener CSV loaded from {latest!r}, but it has 0 rows.")
    st.stop()

# Normalize key string columns that we care about
for col in ("name", "symbol", "ticker", "Ticker", "Symbol", "tv", "tradingview"):
    if col in df.columns:
        df[col] = df[col].apply(_safe_str)

# Build/repair the 'ticker' column
if "ticker" not in df.columns:
    df["ticker"] = df.apply(resolve_ticker, axis=1)
else:
    # Fill blank/whitespace tickers from other fields
    mask_blank = df["ticker"].apply(_safe_str).eq("")
    if mask_blank.any():
        df.loc[mask_blank, "ticker"] = df.loc[mask_blank].apply(resolve_ticker, axis=1)

# Final tidy
df["ticker"] = df["ticker"].apply(_safe_str).str.upper()

# Diagnostics for missing tickers (non-fatal)
missing = df["ticker"].eq("")
if missing.any():
    st.warning(f"{missing.sum()} rows have no ticker after cleanup. Showing a sample below.")
    st.dataframe(df[missing].head(10), use_container_width=True, hide_index=True)

st.caption(f"SCREENER_FIX v1.4 • Source: {latest} • Rows: {len(df):,}")

# Show the table
st.dataframe(df, use_container_width=True, hide_index=True)
