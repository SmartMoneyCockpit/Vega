# pages/04_Screener_Text.py
import os
import glob
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Screener — Text", layout="wide")
st.title("Screener — Text")

def _safe_str(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def resolve_ticker(row: pd.Series) -> str:
    name   = _safe_str(row.get("name", ""))
    symbol = _safe_str(row.get("symbol", ""))
    tick   = _safe_str(row.get("ticker", ""))
    primary = tick or symbol
    if primary:
        return primary
    if "(" in name and ")" in name:
        inside = name.split("(")[-1].split(")")[0].strip()
        if inside:
            return inside
    if " - " in name:
        left = name.split(" - ", 1)[0].strip()
        if left and all(c.isupper() or c == "." for c in left):
            return left
    return ""

def _load_latest_csv():
    candidates = []
    candidates += glob.glob("data/snapshots/*/*screener*.csv", recursive=True)
    candidates += glob.glob("data/*screener*.csv", recursive=True)
    candidates += glob.glob("reports/*screener*.csv", recursive=True)
    candidates += glob.glob("output/*screener*.csv", recursive=True)
    candidates += glob.glob("*.csv")
    for path in candidates:
        try:
            df = pd.read_csv(path)
            if len(df.columns) > 0:
                return df, path
        except Exception:
            continue
    return pd.DataFrame(), None

df, source_path = _load_latest_csv()

if df.empty:
    st.info("No screener CSV found yet. Once the workflow drops a screener CSV, this page will render it.")
    st.stop()

for col in ["name", "symbol", "ticker"]:
    if col in df.columns:
        df[col] = df[col].apply(_safe_str)

if "ticker" not in df.columns or df["ticker"].eq("").all():
    df["ticker"] = df.apply(resolve_ticker, axis=1)
else:
    mask_blank = df["ticker"].astype(str).str.strip().eq("")
    if mask_blank.any():
        df.loc[mask_blank, "ticker"] = df[mask_blank].apply(resolve_ticker, axis=1)

left, right = st.columns([0.7, 0.3])
with left:
    st.caption(f"Source: {source_path or 'unknown'} — Rows: {len(df):,}")
with right:
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                       file_name="screener_clean.csv", mime="text/csv")

st.dataframe(df, use_container_width=True, hide_index=True)
