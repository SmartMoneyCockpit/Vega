import re
import streamlit as st
import pandas as pd
from modules.utils.data_remote import load_csv_auto
from modules.utils.tv_links import tv_symbol_url

st.set_page_config(page_title="Screener — Text", layout="wide")
st.title("Screener — Text")

# Name → ticker fallbacks for common cases
NAME_TO_TICKER = {
    "SPDR S&P 500 ETF": "SPY",
    "Invesco QQQ Trust": "QQQ",
    "iShares Russell 2000": "IWM",
    "BMO Growth ETF": "ZGRO.TO",
    "iShares S&P/TSX Canadian Dividend Aristocrats Index ETF": "CDZ.TO",
}

def clean_ticker(value: str) -> str:
    """Very permissive cleanup: keep letters/numbers/.-:/, uppercase."""
    if not value: return ""
    s = re.sub(r"[^A-Za-z0-9\.\-:]", "", str(value).upper())
    # If we accidentally got a long fund name, this will still look wrong; a fallback map fixes the common ETFs.
    return s

def resolve_ticker(row: pd.Series) -> str:
    """Pick the best ticker: ticker column > symbol column > fallback by name."""
    # 1) explicit ticker column if present
    t = row.get("ticker")
    if isinstance(t, str) and t.strip():
        return clean_ticker(t)
    # 2) symbol column (expect ticker here ideally)
    s = row.get("symbol")
    if isinstance(s, str) and s.strip():
        # if it looks like a long name, try fallback
        if " " in s.strip():
            # try name map
            n = row.get("name", "").strip()
            if n in NAME_TO_TICKER:
                return NAME_TO_TICKER[n]
        return clean_ticker(s)
    # 3) fallback by name
    n = row.get("name", "").strip()
    if n in NAME_TO_TICKER:
        return NAME_TO_TICKER[n]
    return clean_ticker(n[:8])  # last resort (still gives something linkable)

# Load screener rows (vega-data)
df = load_csv_auto("data/screener.csv")
if df.empty:
    st.info("No screener data yet. Place a CSV at **vega-data/data/screener.csv**.")
    st.caption("Columns: symbol,name,price,rs,grade,decision,macro,fundamentals,technicals,options,risk,contras,earnings,tariff,notes")
    st.stop()

# Resolve a reliable 'ticker' column for links/joins
df = df.copy()
df["ticker"] = df.apply(resolve_ticker, axis=1)

# Load quotes (hourly, from vega-data)
quotes = load_csv_auto("data/screener_quotes.csv")
if not quotes.empty:
    # expected: ticker,last,vol,chg,chg_pct,ts
    quotes["ticker"] = quotes["ticker"].astype(str).str.upper()
    df = df.merge(quotes, on="ticker", how="left")

st.write("### Results")
for _, r in df.iterrows():
    ticker = str(r.get("ticker", "")).strip()
    display_name = str(r.get("name") or r.get("symbol") or ticker)

    cols = st.columns([3, 1.2, 1.2, 1.2, 1.2, 1.4])
    with cols[0]:
        # Text shows the friendly name; link goes to ticker
        st.markdown(f"[**{display_name}** ↗]({tv_symbol_url(ticker)})", unsafe_allow_html=True)
        st.caption(ticker)
    with cols[1]:  # Last
        last = r.get("last", r.get("price", "—"))
        st.write(last if last != "" else "—")
    with cols[2]:  # Vol
        st.write(r.get("vol", "—"))
    with cols[3]:  # Chg
        st.write(r.get("chg", "—"))
    with cols[4]:  # % Chg
        pct = r.get("chg_pct", None)
        st.write(f"{pct:.2f}%" if isinstance(pct, (int, float)) else "—")
    with cols[5]:
        st.write(r.get("decision", "—"))

    with st.expander(f"A-to-Z Quickview — {display_name}"):
        st.write({
            "Macro/Sector": r.get("macro",""),
            "Fundamentals": r.get("fundamentals",""),
            "MTF Technicals": r.get("technicals",""),
            "Options (POP 60%, 21–90 DTE)": r.get("options",""),
            "Risk/Targets": r.get("risk",""),
            "Contras/Hedges": r.get("contras",""),
            "Earnings Window": r.get("earnings",""),
            "Tariff/USMCA": r.get("tariff",""),
            "Notes": r.get("notes","")
        })
