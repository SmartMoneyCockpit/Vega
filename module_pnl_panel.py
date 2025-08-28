# -*- coding: utf-8 -*-
"""
PnL & Risk Breakdown Panel — Vega Trading Cockpit
- Reads data/trades.csv (or creates demo if missing)
- KPIs: PnL $, Win rate, Avg R, Expectancy, Max DD (basic)
- Breakdowns: by week, strategy, ticker
- Charts: Equity curve, Weekly PnL
Schema expected (headers, case-insensitive accepted):
date, ticker, side, strategy, qty, entry, stop, exit, fees, notes
Optional: r_multiple, rr_planned
"""
from __future__ import annotations
import os, io, math, datetime as dt
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = "data"
TRADES_CSV = os.path.join(DATA_DIR, "trades.csv")
os.makedirs(DATA_DIR, exist_ok=True)

DEMO_ROWS = [
    # date, ticker, side, strategy, qty, entry, stop, exit, fees, notes, r_multiple, rr_planned
    ["2025-08-20","SPY","LONG","Breakout",100, 500.00, 490.00, 510.00, 2.00,"demo", 1.0, 2.0],
    ["2025-08-21","QQQ","LONG","Pullback",80, 450.00, 441.00, 446.00, 2.00,"demo", -0.5, 2.5],
    ["2025-08-22","IWM","SHORT","Reversal",-60, 210.00, 214.00, 202.00, 2.00,"demo", 2.0, 2.0],
    ["2025-08-25","AAPL","LONG","Breakout",50, 195.00, 190.00, 201.00, 1.50,"demo", 1.2, 3.0],
    ["2025-08-26","MSFT","LONG","Trend",40, 430.00, 420.00, 425.00, 1.50,"demo", -0.5, 2.0],
]

def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    m = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=m)
    # ensure required columns exist
    for col in ["date","ticker","side","strategy","qty","entry","stop","exit","fees"]:
        if col not in df.columns:
            df[col] = np.nan
    # friendly types
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    for col in ["qty","entry","stop","exit","fees","r_multiple","rr_planned"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan
    df["side"] = df["side"].str.upper().fillna("")
    return df

def _ensure_demo():
    if not os.path.exists(TRADES_CSV):
        pd.DataFrame(DEMO_ROWS, columns=["date","ticker","side","strategy","qty","entry","stop","exit","fees","notes","r_multiple","rr_planned"]).to_csv(TRADES_CSV, index=False)

def _load_trades() -> pd.DataFrame:
    if not os.path.exists(TRADES_CSV):
        _ensure_demo()
    try:
        df = pd.read_csv(TRADES_CSV)
    except Exception:
        _ensure_demo()
        df = pd.read_csv(TRADES_CSV)
    return _normalize_cols(df)

def _equity_curve(df: pd.DataFrame) -> pd.DataFrame:
    # Risk/unit = |entry-stop|; PnL$ = (exit-entry)*qty - fees; R = PnL$/Risk$
    df = df.copy()
    risk_per = (df["entry"] - df["stop"]).abs()
    pnl_dollars = (df["exit"] - df["entry"]) * df["qty"] - df["fees"].fillna(0.0)
    # if qty negative (short), sign already in qty covers direction
    # fallback R multiple if provided
    r_from_price = np.where(risk_per>0, pnl_dollars/np.where(risk_per>0, risk_per*df["qty"].abs().replace(0,np.nan), np.nan), np.nan)
    r = df["r_multiple"].where(df["r_multiple"].notna(), r_from_price)
    df["r_multiple"] = r
    df["pnl"] = pnl_dollars
    df = df.sort_values("date")
    df["equity"] = df["pnl"].cumsum()
    return df[["date","ticker","strategy","pnl","r_multiple","equity"]]

def _basic_kpis(df: pd.DataFrame):
    wins = (df["pnl"]>0).sum()
    losses = (df["pnl"]<0).sum()
    total = len(df)
    win_rate = wins/total*100 if total>0 else 0.0
    avg_r = df["r_multiple"].replace([np.inf,-np.inf], np.nan).dropna().mean()
    expectancy = df["pnl"].mean()
    # max drawdown (naive)
    eq = df["equity"].fillna(0).values
    peak, mdd = 0.0, 0.0
    for x in eq:
        peak = max(peak, x)
        mdd = min(mdd, x-peak)
    return {
        "trades": int(total),
        "win_rate": win_rate,
        "avg_r": float(0.0 if np.isnan(avg_r) else avg_r),
        "expectancy": float(0.0 if np.isnan(expectancy) else expectancy),
        "total_pnl": float(df["pnl"].sum()),
        "max_dd": float(mdd)
    }

def render_pnl_panel():
    st.header("PnL & Risk Breakdown Panel")
    st.caption("Reads **data/trades.csv**. You can upload to append or overwrite.")
    df = _load_trades()
    if df.empty:
        st.warning("No trades found.")
        return

    # Upload to replace file
    up = st.file_uploader("Upload trades.csv (same headers) to replace existing", type=["csv"])
    if up:
        new = pd.read_csv(up)
        _normalize_cols(new).to_csv(TRADES_CSV, index=False)
        st.success("Uploaded & replaced. Refresh to see updates.")

    cur = _equity_curve(df)
    k = _basic_kpis(cur)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Trades", k["trades"])
    c2.metric("Win Rate", f"{k['win_rate']:.1f}%")
    c3.metric("Avg R", f"{k['avg_r']:.2f}x")
    c4.metric("Expectancy (avg $/trade)", f"${k['expectancy']:.2f}")
    c5.metric("Total PnL ($)", f"${k['total_pnl']:.2f}")

    st.line_chart(cur.set_index(pd.to_datetime(cur["date"]))["equity"], height=200)
    st.bar_chart(cur.groupby(pd.to_datetime(cur["date"]).to_period("W")).sum(numeric_only=True)["pnl"], height=200)

    st.subheader("Breakdowns")
    by = st.selectbox("Group by", ["strategy","ticker","week"], index=0)
    if by == "week":
        g = cur.groupby(pd.to_datetime(cur["date"]).to_period("W")).agg({"pnl":"sum","r_multiple":"mean"}).rename_axis("week").reset_index()
    else:
        g = cur.groupby(by).agg({"pnl":"sum","r_multiple":"mean"}).reset_index()
    st.dataframe(g, use_container_width=True)
