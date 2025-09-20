
import os, json, math, streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ticker — VectorVest Detail", layout="wide")

st.title("Ticker — VectorVest Detail (No Plotly)")
st.caption("Per‑ticker VectorVest metrics + trend deltas (1w, 1m, 3m, 6m, 1y) and charts")

def load_signals():
    p = os.path.join("vault","cache","vectorvest_signals.json")
    if not os.path.exists(p):
        return pd.DataFrame()
    try:
        data = json.load(open(p,"r",encoding="utf-8"))
        df = pd.DataFrame(data.get("signals", []))
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
    fn = {"vst": f"{symbol}.csv", "eps": f"{symbol}_eps.csv", "growth": f"{symbol}_growth.csv", "sales_growth": f"{symbol}_sales_growth.csv"}[metric]
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        return pd.DataFrame()
    try:
        df = pd.read_csv(p)
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns or metric not in df.columns:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df[["date", metric]]
    except Exception:
        return pd.DataFrame()

def pct_change(series: pd.Series, periods: int):
    if len(series) <= periods or periods <= 0: return None
    try:
        now = float(series.iloc[-1]); past = float(series.iloc[-periods-1])
        if past != 0: return 100.0*(now - past)/abs(past)
    except Exception:
        return None
    return None

def format_delta(x):
    if x is None: return "—"
    return f"{'▲' if x>=0 else '▼'} {x:+.2f}%"

def plot_metric(df, metric, title, weeks=26, bands=False):
    if df.empty:
        st.info(f"No timeseries for {metric.upper()} — drop CSVs into vault/timeseries/vv/"); return
    d = df.tail(weeks).copy()
    d["ma4"] = d[metric].rolling(4, min_periods=1).mean()
    d["ma12"] = d[metric].rolling(12, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(7,3))
    if bands:
        ax.axhspan(1.2, 2.0, alpha=0.09)
        ax.axhspan(0.9, 1.19, alpha=0.10)
        ax.axhspan(0.0, 0.89, alpha=0.08)
    ax.plot(d["date"], d[metric], label=metric.upper())
    ax.plot(d["date"], d["ma4"], label="MA 4w")
    ax.plot(d["date"], d["ma12"], label="MA 12w")
    ax.set_title(title); ax.set_xlabel("Date"); ax.set_ylabel(metric.upper())
    ax.legend(loc="best", fontsize="small")
    st.pyplot(fig, clear_figure=True)

signals = load_signals()
symbols = list(signals.get("symbol", pd.Series([])).dropna().astype(str).unique())

col1, col2 = st.columns([3,2])
with col1:
    sym = st.selectbox("Symbol", symbols, index=0 if symbols else None, placeholder="Select a symbol")
    custom = st.text_input("Override symbol (optional)", value="")
    symbol = (custom.strip().upper() if custom.strip() else (sym or "")).upper()
    period = st.select_slider("Chart window", options=["26w","52w"], value="26w")
with col2:
    st.markdown("**TradingView**")
    tv_template = os.getenv("TV_EMBED_TEMPLATE", "")
    if tv_template and symbol:
        url = tv_template.replace("{SYMBOL}", symbol)
        st.components.v1.iframe(url, height=360, scrolling=True)
    elif symbol:
        st.link_button("Open on TradingView", f"https://www.tradingview.com/symbols/{symbol}/")

if not symbol: st.stop()

st.subheader(f"Current VectorVest snapshot — {symbol}")
snap = signals[signals["symbol"].astype(str).str.upper() == symbol]
if snap.empty:
    st.info("Symbol is not in your signals cache. Add it to vault/cache/vectorvest_signals.json.")
else:
    st.dataframe(snap, use_container_width=True)

st.subheader("Trend — is it going up or down?")
weeks_map = {"1w":1, "1m":4, "3m":13, "6m":26, "1y":52}
rows = []
for m in ["vst","eps","growth","sales_growth"]:
    ser_df = load_series(symbol, m)
    if ser_df.empty:
        rows.append({"metric": m.upper(), **{k:'—' for k in weeks_map}}); continue
    vals = ser_df[m]; row = {"metric": m.upper()}
    for k,w in weeks_map.items(): row[k] = format_delta(pct_change(vals, w))
    rows.append(row)
delta_df = pd.DataFrame(rows, columns=["metric"]+list(weeks_map.keys()))
st.dataframe(delta_df, use_container_width=True)

st.subheader("Charts")
w = 26 if period=="26w" else 52
tab1,tab2,tab3,tab4 = st.tabs(["VST","EPS","Earnings Growth","Sales Growth"])
with tab1: plot_metric(load_series(symbol,"vst"), "vst", f"VST — {symbol}", weeks=w, bands=True)
with tab2: plot_metric(load_series(symbol,"eps"), "eps", f"EPS — {symbol}", weeks=w)
with tab3: plot_metric(load_series(symbol,"growth"), "growth", f"Earnings Growth (%) — {symbol}", weeks=w)
with tab4: plot_metric(load_series(symbol,"sales_growth"), "sales_growth", f"Sales Growth (%) — {symbol}", weeks=w)
