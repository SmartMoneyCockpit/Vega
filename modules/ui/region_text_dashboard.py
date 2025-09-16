import streamlit as st, pandas as pd
from pathlib import Path
from modules.utils.tv_links import tv_symbol_url
from modules.ui.focus_chart import render_focus

def load_csv(p):
    try: return pd.read_csv(p)
    except Exception: return pd.DataFrame()

def render_region(region: str, collapse_focus=True):
    region = region.upper()
    st.subheader(f"{region} Index Dashboard")
    focus_default = "SPY" if region=="NA" else ("VGK" if region=="EU" else "EWJ")
    focus_symbol = st.session_state.get("focus_symbol", focus_default)
    render_focus(focus_symbol, collapsed=collapse_focus)

    df = load_csv(f"data/snapshots/{region.lower()}_indices.csv")
    if df.empty:
        st.info("No snapshot data yet. The hourly worker will populate CSVs.")
        return

    def trend_row(r):
        a = "A" if r.get("above_50d") else "B"
        b = "A" if r.get("above_200d") else "B"
        s = r.get("sma50_slope","Flat")
        return f"{a}50/{b}200 • {s}"

    if "rs" in df.columns:
        df["rs_flag"] = df["rs"].apply(lambda x: "▲" if x>0 else "▼" if x<0 else "•")
    else:
        df["rs_flag"] = "•"
    df["trend"] = df.apply(trend_row, axis=1)
    df["decision"] = df["decision"].fillna("🟡 Wait")

    st.write("### Index Scorecard")
    for _, r in df.iterrows():
        sym = r["symbol"]
        cols = st.columns([2,1,1,1,2,2])
        with cols[0]: st.markdown(f"[**{sym}** ↗]({tv_symbol_url(sym)})", unsafe_allow_html=True)
        with cols[1]: st.write(r.get("price"))
        with cols[2]: st.write(r.get("chg_1d"))
        with cols[3]: st.write(r.get("rs_flag"))
        with cols[4]: st.write(r.get("trend"))
        with cols[5]: st.write(r.get("decision"))
        with st.expander(f"Details — {sym}"):
            st.write({
                "1W%": r.get("chg_1w"),
                "1M%": r.get("chg_1m"),
                "YTD%": r.get("ytd"),
                "%>50D": r.get("breadth_50"),
                "%>200D": r.get("breadth_200"),
                "ATR%": r.get("atr_pct"),
                "Momentum(10>30)": r.get("mom_flag"),
                "Room to R/S (ATRs)": r.get("room_atr"),
                "Earnings window": r.get("earnings_window","N/A"),
                "Contras": r.get("contras","")
            })
            if st.button(f"Preview {sym} in Focus", key=f"focus_{sym}"):
                st.session_state["focus_symbol"] = sym
                st.experimental_rerun()

    # Sector movers
    st.write("### Sector Movers")
    sec = load_csv(f"data/snapshots/{region.lower()}_sectors.csv")
    if not sec.empty: st.dataframe(sec, use_container_width=True, hide_index=True)
    else: st.caption("No sector snapshot yet.")

    # FX & Commodities
    st.write("### FX & Commodities")
    fxf = Path(f"data/snapshots/{region.lower()}_fxcmd.csv")
    if fxf.exists():
        fx = pd.read_csv(fxf)
        fx["link"] = fx["symbol"].apply(tv_symbol_url)
        fx["symbol"] = fx.apply(lambda x: f"[{x['symbol']}]({x['link']})", axis=1)
        fx = fx.drop(columns=["link"])
        st.markdown(fx.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.caption("No FX/commodities snapshot yet.")

    rp = Path(f"reports/{region}/latest.md")
    if rp.exists():
        st.write("### Daily Report")
        st.markdown(rp.read_text())
    else:
        st.caption("No report generated yet.")
