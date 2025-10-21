import streamlit as st
import pandas as pd

try:
    from modules.risk.risk_scoring import full_report
    from data.eodhd_adapter import get_eod_prices_csv
except Exception as _ex:
    full_report = None
    get_eod_prices_csv = None

def _risk_for(symbol: str, period: str="1y", benchmark: str|None="SPY"):
    if (full_report is None) or (get_eod_prices_csv is None):
        return {}
    df = get_eod_prices_csv(symbol, period=period)
    col = "adjusted_close" if "adjusted_close" in df.columns else "close"
    prices = df.set_index("date")[col]
    bench = None
    if benchmark:
        bf = get_eod_prices_csv(benchmark, period=period)
        bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
        bench = bf.set_index("date")[bcol]
    return full_report(prices, bench)

def render():
    st.header('PnL & Risk Breakdown')
    st.caption("Adds Sharpe, Sortino, Volatility, Max Drawdown, CVaR, CAGR, and a 0–100 composite score from the Vega Risk Engine.")

    symbols = st.text_input("Symbols (comma-separated)", value="SPY, QQQ, IWM")
    benchmark = st.text_input("Benchmark", value="SPY")
    period = st.selectbox("Lookback", ["6m","1y","2y","3y","5y"], index=1)
    if st.button("Compute Risk Columns"):
        rows = []
        for s in [x.strip() for x in symbols.split(",") if x.strip()]:
            met = _risk_for(s, period=period, benchmark=benchmark)
            rows.append({
                "Symbol": s,
                "Sharpe": met.get("sharpe"),
                "Sortino": met.get("sortino"),
                "Volatility": met.get("volatility"),
                "MaxDD": met.get("max_drawdown"),
                "CVaR": met.get("cvar"),
                "CAGR": met.get("cagr"),
                "Score": met.get("score"),
                "Beta": met.get("beta"),
            })
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
