# src/pages/04_Screener_Text.py
import os, glob, math
import pandas as pd
import streamlit as st

# Optional helper (safe to ignore if module doesn't exist)
try:
    from modules.data.remote import load_csv_auto  # optional
except Exception:
    load_csv_auto = None

st.set_page_config(page_title="Screener — Text v1.7", layout="wide")
st.title("Screener — Text v1.7")

# -----------------------------
# Safe string helper
# -----------------------------
def _safe_str(x) -> str:
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

# -----------------------------
# Ticker resolver (robust)
# -----------------------------
def resolve_ticker(row: pd.Series) -> str:
    # Prefer explicit columns first
    for key in ("ticker", "symbol", "Ticker", "Symbol", "tv", "tradingview"):
        if key in row:
            s = _safe_str(row[key])
            if s:
                return s.upper()

    name = _safe_str(row.get("name", ""))  # never call .strip() on non-str
    # NAME (TICKER)
    if "(" in name and ")" in name:
        inside = name.split("(")[-1].split(")")[0].strip()
        if inside:
            return inside.upper()
    # TICKER - Company Name
    if " - " in name:
        left = name.split(" - ", 1)[0].strip()
        if left and all(ch.isupper() or ch.isdigit() or ch == "." for ch in left):
            return left.upper()
    return ""

# -----------------------------
# File discovery / loading
# -----------------------------
def _find_latest_file():
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

def _load_csv_latest() -> tuple[pd.DataFrame, str | None]:
    # Prefer your project helper if present
    if load_csv_auto is not None:
        try:
            df, path = load_csv_auto(pattern="*screener*.csv")
            if df is not None and not df.empty:
                return df, path
        except Exception:
            pass

    latest = _find_latest_file()
    if not latest:
        return pd.DataFrame(), None
    try:
        df = pd.read_csv(latest, keep_default_na=False, na_filter=True, low_memory=False)
    except Exception:
        df = pd.read_csv(latest)
    return df, latest

# -----------------------------
# Main
# -----------------------------
df, source_path = _load_csv_latest()
if df is None or df.empty:
    st.info("No screener CSV found yet. Once the workflow drops a screener CSV, this page will render it.")
    st.stop()

# Normalize potential columns we’ll read
for col in ("name", "symbol", "ticker", "Ticker", "Symbol", "tv", "tradingview"):
    if col in df.columns:
        df[col] = df[col].apply(_safe_str)

# Create/repair ticker column
if "ticker" not in df.columns:
    df["ticker"] = df.apply(resolve_ticker, axis=1)
else:
    blank = df["ticker"].apply(_safe_str).eq("")
    if blank.any():
        df.loc[blank, "ticker"] = df.loc[blank].apply(resolve_ticker, axis=1)

df["ticker"] = df["ticker"].apply(_safe_str).str.upper()

# Non-fatal diagnostics for unresolved rows
missing = df["ticker"].eq("")
if missing.any():
    st.warning(f"{missing.sum()} rows have no ticker after cleanup. Showing a sample below.")
    st.dataframe(df[missing].head(10), use_container_width=True, hide_index=True)

# ---- Clean + quick tools -----------------------------------------------------
# keep only rows with a ticker, de-dupe by ticker
df_clean = df[df["ticker"] != ""].drop_duplicates(subset=["ticker"]).reset_index(drop=True)

# search box (matches ticker OR name)
q = st.text_input("Filter (ticker or name)").strip()
if q:
    df_view = df_clean[
        df_clean["ticker"].str.contains(q, case=False, na=False)
        | df_clean.get("name", pd.Series("", index=df_clean.index)).str.contains(q, case=False, na=False)
    ]
else:
    df_view = df_clean

# small stats
c1, c2 = st.columns(2)
c1.metric("Rows (raw)", len(df))
c2.metric("Rows (clean)", len(df_view))

# download cleaned CSV
st.download_button(
    "Download cleaned CSV",
    data=df_view.to_csv(index=False).encode("utf-8"),
    file_name="screener_clean.csv",
    mime="text/csv",
)

# show cleaned/filtered table
st.dataframe(df_view, use_container_width=True, hide_index=True)

# Footer caption
st.caption(f"SCREENER_FIX v1.7 • Source: {source_path or 'unknown'} • Rows(raw): {len(df):,} • Rows(clean): {len(df_view):,}")

# Optional: diagnostics of discovered files
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
