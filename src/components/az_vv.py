
import os, json, math, streamlit as st
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _load_signals_df():
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

def _load_series(symbol: str, metric: str):
    base = os.path.join("vault","timeseries","vv")
    fn = {"vst": f"{symbol}.csv","eps": f"{symbol}_eps.csv","growth": f"{symbol}_growth.csv","sales_growth": f"{symbol}_sales_growth.csv"}[metric]
    p = os.path.join(base, fn)
    if not os.path.exists(p): 
        return pd.DataFrame()
    try:
        df = pd.read_csv(p)
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns: return pd.DataFrame()
        if metric not in df.columns:
            if metric != "vst" or "vst" not in df.columns:
                return pd.DataFrame()
        col = metric if metric in df.columns else "vst"
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df[["date", col]].rename(columns={col: metric})
    except Exception:
        return pd.DataFrame()

def _pct_change(series, periods: int):
    if len(series) <= periods or periods <= 0: return None
    try:
        now = float(series.iloc[-1]); past = float(series.iloc[-periods-1])
        if past != 0: return 100.0*(now - past)/abs(past)
    except Exception:
        return None
    return None

def _fmt_delta(x):
    if x is None: return "—"
    return f"{'▲' if x>=0 else '▼'} {x:+.2f}%"

def render_vv_block(symbol: str, window: str = "26w"):
    if not symbol:
        st.info("No symbol selected for VectorVest block."); return
    symbol = symbol.upper()
    st.markdown(f"### VectorVest — {symbol}")
    signals = _load_signals_df()
    snap = signals[signals.get("symbol","").astype(str).str.upper() == symbol]
    if snap.empty:
        st.warning("No VectorVest snapshot found for this symbol (vectorvest_signals.json).")
    else:
        st.dataframe(snap, use_container_width=True)

    weeks_map = {"1w":1, "1m":4, "3m":13, "6m":26, "1y":52}
    rows = []
    for m in ["vst","eps","growth","sales_growth"]:
        ser = _load_series(symbol, m)
        if ser.empty:
            rows.append({"metric": m.upper(), **{k:'—' for k in weeks_map}}); continue
        vals = ser[m]; row = {"metric": m.upper()}
        for k,w in weeks_map.items(): row[k] = _fmt_delta(_pct_change(vals, w))
        rows.append(row)
    delta_df = pd.DataFrame(rows, columns=["metric"]+list(weeks_map.keys()))
    st.dataframe(delta_df, use_container_width=True)

    w = 26 if (window or "26w").lower().startswith("26") else 52
    tab1,tab2,tab3,tab4 = st.tabs(["VST","EPS","Earnings Growth","Sales Growth"])

    def _plot(df, metric, title, bands=False):
        if df.empty:
            st.info(f"No timeseries for {metric.upper()} — add CSVs to vault/timeseries/vv/"); return
        d = df.tail(w).copy()
        d["ma4"] = d[metric].rolling(4, min_periods=1).mean()
        d["ma12"] = d[metric].rolling(12, min_periods=1).mean()
        try:
            fig, ax = plt.subplots(figsize=(7,3))
            if bands:
                ax.axhspan(1.2,2.0,alpha=0.09); ax.axhspan(0.9,1.19,alpha=0.10); ax.axhspan(0.0,0.89,alpha=0.08)
            ax.plot(d["date"], d[metric], label=metric.upper())
            ax.plot(d["date"], d["ma4"], label="MA 4w")
            ax.plot(d["date"], d["ma12"], label="MA 12w")
            ax.set_title(title); ax.set_xlabel("Date"); ax.set_ylabel(metric.upper()); ax.legend(loc="best", fontsize="small")
            st.pyplot(fig, clear_figure=True)
        except Exception:
            st.line_chart(d.set_index("date")[[metric]])

    with tab1: _plot(_load_series(symbol,"vst"), "vst", f"VST — {symbol}", bands=True)
    with tab2: _plot(_load_series(symbol,"eps"), "eps", f"EPS — {symbol}")
    with tab3: _plot(_load_series(symbol,"growth"), "growth", f"Earnings Growth (%) — {symbol}")
    with tab4: _plot(_load_series(symbol,"sales_growth"), "sales_growth", f"Sales Growth (%) — {symbol}")
