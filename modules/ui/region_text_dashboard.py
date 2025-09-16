import streamlit as st
import pandas as pd
from pathlib import Path

from modules.utils.tv_links import tv_symbol_url
from modules.ui.focus_chart import render_focus  # toggle-based: render_focus(symbol)

def load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def render_region(region: str) -> None:
    """
    Text-first dashboard with compact rows + click-to-expand details.
    One optional TradingView focus chart is gated behind a toggle in render_focus().
    """
    region = region.upper()
    st.subheader(f"{region} Index Dashboard")

    # Load snapshot (may be empty on first run)
    snap_path = f"data/snapshots/{region.lower()}_indices.csv"
    df = load_csv(snap_path)

    # Choose a sensible default symbol
    focus_default = "SPY" if region == "NA" else ("VGK" if region == "EU" else "EWJ")
    if not df.empty and "symbol" in df.columns and pd.notna(df.iloc[0]["symbol"]):
        focus_default = str(df.iloc[0]["symbol"])

    # Persist and render the (toggle-based) focus chart
    st.session_state.setdefault("focus_symbol", focus_default)
    render_focus(st.session_state["focus_symbol"])

    if df.empty:
        st.info("No snapshot data yet. The hourly worker will populate CSVs.")
        return

    # ----- Helpers for compact row fields -----
    def _rs_flag(x):
        try:
            v = float(x)
            return "▲" if v > 0 else "▼" if v < 0 else "•"
        except Exception:
            return "•"

    def _trend_row(row):
        above_50 = bool(row.get("above_50d", False))
        above_200 = bool(row.get("above_200d", False))
        slope = row.get("sma50_slope", "Flat")
        a = "A" if above_50 else "B"
        b = "A" if above_200 else "B"
        return f"{a}50/{b}200 • {slope}"

    if "rs" in df.columns:
        df["rs_flag"] = df["rs"].apply(_rs_flag)
    else:
        df["rs_flag"] = "•"

    df["trend"] = df.apply(_trend_row, axis=1)
    if "decision" not in df.columns:
        df["decision"] = "🟡 Wait"
    else:
        df["decision"] = df["decision"].fillna("🟡 Wait")

    # ----- Index Scorecard (compact rows + expanders) -----
    st.write("### Index Scorecard")
    for _, r in df.iterrows():
        sym = str(r.get("symbol", ""))
        cols = st.columns([2, 1, 1, 1, 2, 2])
        with cols[0]:
            st.markdown(f"[**{sym}** ↗]({tv_symbol_url(sym)})", unsafe_allow_html=True)
        with cols[1]:
            st.write(r.get("price", "—"))
        with cols[2]:
            st.write(r.get("chg_1d", "—"))
        with cols[3]:
            st.write(r.get("rs_flag", "•"))
        with cols[4]:
            st.write(r.get("trend", "—"))
        with cols[5]:
            st.write(r.get("decision", "🟡 Wait"))

        with st.expander(f"Details — {sym}"):
            details = {
                "1W%": r.get("chg_1w"),
                "1M%": r.get("chg_1m"),
                "YTD%": r.get("ytd"),
                "%>50D": r.get("breadth_50"),
                "%>200D": r.get("breadth_200"),
                "ATR%": r.get("atr_pct"),
                "Momentum(10>30)": r.get("mom_flag"),
                "Room to R/S (ATRs)": r.get("room_atr"),
                "Earnings window": r.get("earnings_window", "N/A"),
                "Contras": r.get("contras", "")
            }
            st.write(details)
            if st.button(f"Preview {sym} in Focus", key=f"focus_{sym}"):
                st.session_state["focus_symbol"] = sym
                st.experimental_rerun()

    # ----- Sector movers -----
    st.write("### Sector Movers")
    sec = load_csv(f"data/snapshots/{region.lower()}_sectors.csv")
    if not sec.empty:
        st.dataframe(sec, use_container_width=True, hide_index=True)
    else:
        st.caption("No sector snapshot yet.")

    # ----- FX & Commodities -----
    st.write("### FX & Commodities")
    fx_path = Path(f"data/snapshots/{region.lower()}_fxcmd.csv")
    if fx_path.exists():
        fx = pd.read_csv(fx_path)
        fx["link"] = fx["symbol"].apply(tv_symbol_url)
        fx["symbol"] = fx.apply(lambda x: f"[{x['symbol']}]({x['link']})", axis=1)
        fx = fx.drop(columns=["link"])
        st.markdown(fx.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.caption("No FX/commodities snapshot yet.")

    # ----- Daily report (markdown) -----
    rp = Path(f"reports/{region}/latest.md")
    if rp.exists():
        st.write("### Daily Report")
        st.markdown(rp.read_text())
    else:
        st.caption("No report generated yet.")
