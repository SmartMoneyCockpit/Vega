# modules/ui/region_text_dashboard.py

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.utils.tv_links import tv_symbol_url
from modules.ui.focus_chart import render_focus  # toggle-based: render_focus(symbol)

# --- Remote data fallback (optional) ---
# If local CSVs aren't present (e.g., Render reading from a data branch),
# we'll try to fetch from GitHub raw using these env vars.
REPO_SLUG = os.getenv("VEGA_REPO", "")          # e.g., "SmartMoneyCockpit/Vega"
DATA_BRANCH = os.getenv("VEGA_DATA_BRANCH", "") # e.g., "vega-data"


def _try_read_csv(path: str) -> pd.DataFrame:
    """Read local CSV if it exists, otherwise (optionally) try GitHub raw."""
    p = Path(path)
    # 1) Local file
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    # 2) Remote GitHub raw (only if configured)
    if REPO_SLUG and DATA_BRANCH:
        # Keep same relative path on the data branch
        raw_url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{DATA_BRANCH}/{path}"
        try:
            return pd.read_csv(raw_url)
        except Exception:
            pass
    return pd.DataFrame()


def _rs_flag(x) -> str:
    try:
        v = float(x)
        return "▲" if v > 0 else "▼" if v < 0 else "•"
    except Exception:
        return "•"


def _trend_row(row: pd.Series) -> str:
    above_50 = bool(row.get("above_50d", False))
    above_200 = bool(row.get("above_200d", False))
    slope = row.get("sma50_slope", "Flat")
    a = "A" if above_50 else "B"
    b = "A" if above_200 else "B"
    return f"{a}50/{b}200 • {slope}"


def render_region(region: str) -> None:
    """
    Text-first dashboard with compact rows + click-to-expand details.
    A single TradingView focus chart is gated behind a toggle (render_focus()).
    """
    region = region.upper()
    st.subheader(f"{region} Index Dashboard")

    # Load snapshot (may be empty on first run)
    snap_path = f"data/snapshots/{region.lower()}_indices.csv"
    df = _try_read_csv(snap_path)

    # Choose a sensible default symbol
    focus_default = "SPY" if region == "NA" else ("VGK" if region == "EU" else "EWJ")
    if not df.empty and "symbol" in df.columns and pd.notna(df.iloc[0]["symbol"]):
        focus_default = str(df.iloc[0]["symbol"])

    # Persist & render the (toggle-based) focus chart
    st.session_state.setdefault("focus_symbol", focus_default)
    render_focus(st.session_state["focus_symbol"])

    if df.empty:
        st.info("No snapshot data yet. The hourly worker will populate CSVs.")
        return

    # Compact row fields
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
        sym = str(r.get("symbol", "")).strip()

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
    sec = _try_read_csv(f"data/snapshots/{region.lower()}_sectors.csv")
    if not sec.empty:
        st.dataframe(sec, use_container_width=True, hide_index=True)
    else:
        st.caption("No sector snapshot yet.")

    # ----- FX & Commodities -----
    st.write("### FX & Commodities")
    fx = _try_read_csv(f"data/snapshots/{region.lower()}_fxcmd.csv")
    if not fx.empty:
        fx = fx.copy()
        fx["link"] = fx["symbol"].apply(tv_symbol_url)
        fx["symbol"] = fx.apply(lambda x: f"[{x['symbol']}]({x['link']})", axis=1)
        fx = fx.drop(columns=["link"])
        st.markdown(fx.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.caption("No FX/commodities snapshot yet.")

    # ----- Daily report (markdown) -----
    rp_local = Path(f"reports/{region}/latest.md")
    report_text = None
    if rp_local.exists():
        report_text = rp_local.read_text()
    elif REPO_SLUG and DATA_BRANCH:
        # Try remote report if not present locally
        import requests
        url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{DATA_BRANCH}/reports/{region}/latest.md"
        try:
            resp = requests.get(url, timeout=10)
            if resp.ok:
                report_text = resp.text
        except Exception:
            pass

    if report_text:
        st.write("### Daily Report")
        st.markdown(report_text)
    else:
        st.caption("No report generated yet.")
