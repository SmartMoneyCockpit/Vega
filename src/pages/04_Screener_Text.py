# src/pages/04_Screener_Text.py
import os, glob, math, json
from urllib.parse import quote
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Screener — Text v2.0", layout="wide")
st.title("Screener — Text v2.0")

def _safe_str(x) -> str:
    if isinstance(x, str):
        return x.strip()
    if x is None:
        return ""
    try:
        if isinstance(x, float) and (math.isnan(x) or pd.isna(x)):
            return ""
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def resolve_ticker(row: pd.Series) -> str:
    for c in ("ticker","symbol","Ticker","Symbol","tv","tradingview"):
        if c in row:
            s = _safe_str(row[c])
            if s:
                return s.upper()
    name = _safe_str(row.get("name",""))
    if "(" in name and ")" in name:
        inside = name.split("(")[-1].split(")")[0].strip()
        if inside: return inside.upper()
    if " - " in name:
        left = name.split(" - ",1)[0].strip()
        if left and all(ch.isupper() or ch.isdigit() or ch=="." for ch in left):
            return left.upper()
    return ""

def _find_latest_file():
    pats = [
        "data/snapshots/**/*screener*.csv",
        "data/**/*screener*.csv",
        "reports/**/*screener*.csv",
        "output/**/*screener*.csv",
        "**/*screener*.csv",
    ]
    files=[]
    for p in pats: files += glob.glob(p, recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    if not files: return None
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]

def _load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, keep_default_na=False, na_filter=True, low_memory=False)
    except Exception:
        return pd.read_csv(path)

latest = _find_latest_file()
if not latest:
    st.info("No screener CSV found yet. Once the workflow drops a screener CSV, this page will render it.")
    st.stop()

df = _load_csv(latest)
if df.empty:
    st.info(f"Screener CSV loaded from {latest!r}, but it has 0 rows.")
    st.stop()

for col in ("name","symbol","ticker","Ticker","Symbol","tv","tradingview"):
    if col in df.columns:
        df[col] = df[col].apply(_safe_str)

if "ticker" not in df.columns:
    df["ticker"] = df.apply(resolve_ticker, axis=1)
else:
    blank = df["ticker"].apply(_safe_str).eq("")
    if blank.any():
        df.loc[blank,"ticker"] = df.loc[blank].apply(resolve_ticker, axis=1)

df["ticker"] = df["ticker"].apply(_safe_str).str.upper()

missing = df["ticker"].eq("")
if missing.any():
    st.warning(f"{missing.sum()} rows have no ticker after cleanup. Showing a sample below.")
    st.dataframe(df[missing].head(10), use_container_width=True, hide_index=True)

# ---- Clean + tools
df_clean = df[df["ticker"] != ""].drop_duplicates(subset=["ticker"]).reset_index(drop=True)

q = st.text_input("Filter (ticker or name)").strip()
if q:
    df_view = df_clean[
        df_clean["ticker"].str.contains(q, case=False, na=False)
        | df_clean.get("name", pd.Series("", index=df_clean.index)).str.contains(q, case=False, na=False)
    ]
else:
    df_view = df_clean

# Links
def _tv_url(sym: str) -> str:
    return f"https://www.tradingview.com/chart/?symbol={quote(sym)}"

def _chart_url(sym: str) -> str:
    return f"/TradingView_Charts?symbol={quote(sym)}&interval=D&theme=dark&height=900"

df_view = df_view.copy()
df_view["TradingView"] = df_view["ticker"].apply(_tv_url)
df_view["Chart"] = df_view["ticker"].apply(_chart_url)

# Stats + downloads
c1,c2,c3 = st.columns(3)
c1.metric("Rows (raw)", len(df))
c2.metric("Rows (clean)", len(df_view))
c3.metric("Unique tickers", df_view["ticker"].nunique())

st.download_button(
    "Download cleaned CSV",
    data=df_view.to_csv(index=False).encode("utf-8"),
    file_name="screener_clean.csv",
    mime="text/csv",
)

# Optional quick tickers export
tickers_str = " ".join(df_view["ticker"].tolist())
st.text_area("Tickers (space-separated)", tickers_str, height=70)
st.download_button("Download tickers.txt", tickers_str, file_name="tickers.txt", mime="text/plain")

# Show table
st.dataframe(
    df_view,
    use_container_width=True,
    hide_index=True,
    column_config={
        "TradingView": st.column_config.LinkColumn("TradingView", display_text="Open"),
        "Chart": st.column_config.LinkColumn("Chart", display_text="Open"),
    },
)

st.caption(f"SCREENER_FIX v2.0 • Source: {latest} • Rows(raw): {len(df):,} • Rows(clean): {len(df_view):,}")

with st.expander("Diagnostics"):
    cands = []
    for p in [
        "data/snapshots/**/*screener*.csv",
        "data/**/*screener*.csv",
        "reports/**/*screener*.csv",
        "output/**/*screener*.csv",
        "**/*screener*.csv",
    ]:
        cands += glob.glob(p, recursive=True)
    st.write("Candidates found:", len(cands))
    st.write(sorted([c for c in cands if os.path.isfile(c)])[:50])
