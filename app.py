# app.py — Safe/fast fetch + visible diagnostics
from utils.prefs_bootstrap import prefs  # noqa: F401
import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Vega Cockpit — Core Fix Pack", layout="wide")

# ---- Config / Providers ----
@st.cache_data(show_spinner=False, ttl=900)
def get_config():
    # robust import: don't 500 if schema changed
    try:
        from src.config_schema import load_config
        return load_config("vega_config.yaml")
    except Exception as e:
        return {"_err": f"Config load failed: {e}"}

@st.cache_data(show_spinner=True, ttl=900)
def fetch(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Try primary provider chain, then hard fallback to public/yfinance.
    Never return None — always a DataFrame (possibly empty with 'err' flag).
    """
    try:
        cfg = get_config()
        provider_order = []
        try:
            # prefer configured chain, but enforce a public fallback
            from src.providers import MarketDataProvider
            order = getattr(cfg, "providers", None)
            if order and getattr(order, "order", None):
                provider_order = list(order.order)
            provider_order += ["public"]  # ensure fallback
            provider = MarketDataProvider(provider_order)
            df = provider._fetch(symbol, period, interval)
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception as e:
            # fall through to yfinance path
            st.session_state["_provider_err"] = str(e)

        # Public fallback (direct yfinance) to guarantee a plot
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
        hist = hist.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        return hist.reset_index()

    except Exception as e:
        # return a sentinel DataFrame with error text
        return pd.DataFrame({"__error__":[str(e)]})

def plot_price(df: pd.DataFrame, title: str):
    import plotly.graph_objects as go
    if "__error__" in df.columns:
        st.error(f"Data error: {df['__error__'].iloc[0]}")
        return
    if df.empty:
        st.warning("No data received from any provider.")
        return
    # accept both datetime or named 'Date'
    tcol = "Date" if "Date" in df.columns else df.columns[0]
    fig = go.Figure(data=[go.Candlestick(
        x=df[tcol],
        open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )])
    fig.update_layout(height=520, margin=dict(l=0,r=0,t=30,b=0), title=title)
    st.plotly_chart(fig, use_container_width=True)

# ---- Page body ----
st.title("Vega Cockpit — Core Fix Pack")

cfg = get_config()
if isinstance(cfg, dict) and cfg.get("_err"):
    st.error(cfg["_err"])

tabs = st.tabs(["USA","Canada","Mexico","Europe","APAC"])

with tabs[0]:
    colA, colB = st.columns([1,3])
    with colA:
        symbol = st.text_input("Symbol (Yahoo-style)", value="SPY")
        period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y"], index=2)
        interval = st.selectbox("Interval", ["1d","4h","1h","30m","15m"], index=0)
        st.caption("Public fallback is enabled; provider errors will be shown below.")
        prov_err = st.session_state.get("_provider_err")
        if prov_err:
            st.info(f"Provider chain error observed, using public fallback:\n\n{prov_err}")
    with colB:
        df = fetch(symbol, period, interval)
        plot_price(df, f"{symbol} — {period} / {interval}")
