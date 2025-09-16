from utils.prefs_bootstrap import prefs
# app.py — Vega Cockpit (starter, fast + Render-ready)
import os
import time
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Vega Cockpit", layout="wide")

# -----------------------------
# App Settings / Flags
# -----------------------------
APP_ENV = os.getenv("APP_ENV", "prod")  # dev|prod
st.sidebar.caption(f"Environment: **{APP_ENV}**")

# -----------------------------
# Data (mocked for now; replace with your providers later)
# -----------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_demo(symbol: str = "SPY", n=120) -> pd.DataFrame:
    rng = pd.date_range(end=pd.Timestamp.today(), periods=n, freq="B")
    price = np.cumsum(np.random.normal(loc=0.2, scale=1.5, size=n)) + 500
    df = pd.DataFrame({"date": rng, "close": price})
    df["sma20"] = df["close"].rolling(20).mean()
    df["sma50"] = df["close"].rolling(50).mean()
    return df.dropna()

def plot_price(df: pd.DataFrame, title: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], name="Close"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["sma20"], name="SMA20"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["sma50"], name="SMA50"))
    fig.update_layout(title=title, height=420, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# UI
# -----------------------------
st.title("Vega Cockpit — Core Starter")

tab1, tab2, tab3 = st.tabs(["Dashboard", "Watchlist", "System Check"])

with tab1:
    colA, colB = st.columns(2)
    with colA:
        df_spy = load_demo("SPY")
        plot_price(df_spy, "SPY — Demo (Close + SMA20/50)")
    with colB:
        df_qqq = load_demo("QQQ")
        plot_price(df_qqq, "QQQ — Demo (Close + SMA20/50)")
    st.success("This is a self-contained demo. You can plug in real providers later.")

with tab2:
    st.subheader("Watchlist (demo)")
    wl = pd.DataFrame(
        [
            {"Ticker": "SPY", "Theme": "Hedge / Benchmark", "Status": "🟡 Wait"},
            {"Ticker": "SQQQ", "Theme": "Inverse QQQ", "Status": "🔴 Avoid"},
            {"Ticker": "RWM", "Theme": "Inverse Russell", "Status": "🟡 Wait"},
            {"Ticker": "SLV", "Theme": "Silver", "Status": "🟢 Buy next few days"},
            {"Ticker": "CPER", "Theme": "Copper", "Status": "🟡 Wait"},
        ]
    )
    st.dataframe(wl, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Health / Liveness")
    ok = True
    checks = [
        ("Python version", f"{os.sys.version.split()[0]}", True),
        ("Streamlit", st.__version__, True),
        ("Plotly", go.__version__, True),
        ("ENV PORT (Render sets this)", os.getenv("PORT", "not-set"), True),
    ]
    for name, val, passed in checks:
        st.write(f"**{name}**: `{val}`  — " + ("✅ OK" if passed else "❌ FAIL"))
    if os.getenv("ON_RENDER", "0") == "1":
        st.info("Running on Render.")
    st.write("Sleeping 0.2s to simulate readiness...")
    time.sleep(0.2)
    st.success("System check complete.")
