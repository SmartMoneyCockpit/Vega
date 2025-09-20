
import os, json, math, streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ticker — VectorVest Detail", layout="wide")

st.title("Ticker — VectorVest Detail (Self‑Contained)")
st.caption("Per‑ticker VectorVest metrics + trend deltas (1w, 1m, 3m, 6m, 1y) and chart")

# ---- Helpers ----
def load_signals():
    p = os.path.join("vault","cache","vectorvest_signals.json")
    if not os.path.exists(p):
        return pd.DataFrame()
    try:
        data = json.load(open(p,"r",encoding="utf-8"))
        df = pd.DataFrame(data.get("signals", []))
        # normalize
        ren = {"RT":"rt","RV":"rv","RS":"rs","CI":"ci","EPS":"eps","Growth":"growth","Sales Growth":"sales_growth","salesGrowth":"sales_growth","VST":"vst"}
        for k,v in ren.items():
            if k in df.columns and v not in df.columns:
                df[v] = df[k]
        for c in ["rt","rv","rs","ci","vst","eps","growth","sales_growth","price"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

def load_series(symbol: str, metric: str):
    base = os.path.join("vault","timeseries","vv")
    # vst uses SYMBOL.csv else metric suffix
    fn = {
        "vst": f"{symbol}.csv",
        "eps": f"{symbol}_eps.csv",
        "growth": f"{symbol}_growth.csv",
        "sales_growth": f"{symbol}_sales_growth.csv",
    }[metric]
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        return pd.DataFrame()
    try:
        df = pd.read_csv(p)
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns:
            return pd.DataFrame()
        if metric not in df.columns:
            # handle case vst is the column name in base file
            if metric == "vst" and "vst" in df.columns:
                pass
            else:
                return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df[["date", metric]]
    except Exception:
        return pd.DataFrame()

def pct_change(series: pd.Series, periods: int):
    if len(series) <= periods or periods <= 0:
        return None
    try:
        now = float(series.iloc[-1])
        past = float(series.iloc[-periods-1])
        if math.isfinite(now) and math.isfinite(past) and past != 0:
            return 100.0*(now - past)/abs(past)
    except Exception:
        return None
    return None

def format_delta(x):
    if x is None: return "—"
    arrow = "▲" if x >= 0 else "▼"
    return f"{arrow} {x:+.2f}%"

def plot_metric(df, metric, title, weeks=26):
    if df.empty:
        st.info(f"No timeseries for {metric.upper()} — drop CSVs into vault/timeseries/vv/"); return
    d = df.tail(weeks).copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["date"], y=d[metric], mode="lines", name=metric.upper()))
    # add simple 4/12 week MAs
    d["ma4"] = d[metric].rolling(4, min_periods=1).mean()
    d["ma12"] = d[metric].rolling(12, min_periods=1).mean()
    fig.add_trace(go.Scatter(x=d["date"], y=d["ma4"], mode="lines", name="MA 4w"))
    fig.add_trace(go.Scatter(x=d["date"], y=d["ma12"], mode="lines", name="MA 12w"))
    # bands only for VST
    if metric == "vst":
        for label,(lo,hi),color in [("green",(1.2,2.0),"rgba(34,197,94,0.09)"),
                                    ("yellow",(0.9,1.19),"rgba(234,179,8,0.10)"),
                                    ("red",(0.0,0.89),"rgba(239,68,68,0.08)") ]:
            fig.add_shape(type="rect", xref="paper", yref="y", x0=0, x1=1, y0=lo, y1=hi, fillcolor=color, line_width=0, layer="below")
    fig.update_layout(title=title, height=360, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)

# ---- UI ----
signals = load_signals()
symbols = list(signals.get("symbol", pd.Series([])).dropna().astype(str).unique())
left, right = st.columns([3,2])
with left:
    sym = st.selectbox("Symbol", symbols, index=0 if symbols else None, placeholder="Type or select a symbol")
    custom = st.text_input("Override symbol (optional)", value="", help="Type a symbol to force load even if not in signals list.")
    symbol = (custom.strip().upper() if custom.strip() else (sym or "")).upper()
    period = st.select_slider("Chart window", options=["26w","52w"], value="26w")
with right:
    st.markdown("**TradingView**")
    tv_template = os.getenv("TV_EMBED_TEMPLATE", "")  # e.g., https://s.tradingview.com/widgetembed/?symbol={SYMBOL}&interval=D
    if tv_template and symbol:
        url = tv_template.replace("{SYMBOL}", symbol)
        st.components.v1.iframe(url, height=360, scrolling=True)
    else:
        st.caption("Set env `TV_EMBED_TEMPLATE` to embed charts, or use the link below.")
        if symbol:
            st.link_button("Open on TradingView", f"https://www.tradingview.com/symbols/{symbol}/")

if not symbol:
    st.stop()

# Current snapshot
st.subheader(f"Current VectorVest snapshot — {symbol}")
snap = signals[signals["symbol"].astype(str).str.upper() == symbol]
if snap.empty:
    st.info("Symbol is not in your signals cache. Add it to `vault/cache/vectorvest_signals.json`.")
else:
    st.dataframe(snap, use_container_width=True)

# Trend deltas table
st.subheader("Trend — is it going up or down?")
weeks_map = {"1w":1, "1m":4, "3m":13, "6m":26, "1y":52}
rows = []
for m in ["vst","eps","growth","sales_growth"]:
    ser_df = load_series(symbol, m)
    if ser_df.empty:
        rows.append({"metric": m.upper(), **{k:"—" for k in weeks_map}})
        continue
    vals = ser_df[m]
    row = {"metric": m.upper()}
    for k, w in weeks_map.items():
        row[k] = format_delta(pct_change(vals, w))
    rows.append(row)
delta_df = pd.DataFrame(rows, columns=["metric"]+list(weeks_map.keys()))
st.dataframe(delta_df, use_container_width=True)

# Charts
st.subheader("Charts")
w = 26 if period=="26w" else 52
tab1,tab2,tab3,tab4 = st.tabs(["VST","EPS","Earnings Growth","Sales Growth"])
with tab1:
    plot_metric(load_series(symbol,"vst"), "vst", f"VST — {symbol}", weeks=w)
with tab2:
    plot_metric(load_series(symbol,"eps"), "eps", f"EPS — {symbol}", weeks=w)
with tab3:
    plot_metric(load_series(symbol,"growth"), "growth", f"Earnings Growth (%) — {symbol}", weeks=w)
with tab4:
    plot_metric(load_series(symbol,"sales_growth"), "sales_growth", f"Sales Growth (%) — {symbol}", weeks=w)
