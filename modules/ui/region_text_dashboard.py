import os
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from modules.utils.tv_links import tv_symbol_url
from modules.ui.focus_chart import render_focus
from modules.utils.data_remote import load_csv_auto, github_last_modified, raw_url, github_page_url

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

def _reason_chips(row: pd.Series) -> str:
    chips = []
    try:
        if float(row.get("rs", 0)) > 0: chips.append("RS↑")
    except Exception:
        pass
    if row.get("above_50d"): chips.append(">50D")
    if row.get("above_200d"): chips.append(">200D")
    slope = row.get("sma50_slope", 0)
    try:
        if float(slope) > 0: chips.append("50D slope↑")
    except Exception:
        pass
    try:
        atrp = float(row.get("atr_pct", 0))
        if atrp <= 2.5: chips.append("Vol normal")
        elif atrp > 3.5: chips.append("Vol high")
    except Exception:
        pass
    try:
        room = float(row.get("room_atr", 0))
        if room >= 1.0: chips.append("≥1 ATR room")
    except Exception:
        pass
    return " • ".join(chips)

def _human_lastmod(path_rel: str) -> str:
    lm = github_last_modified(path_rel)
    if lm:
        return f"Updated: {lm}"
    p = Path(path_rel)
    if p.exists():
        ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return f"Updated (local): {ts}"
    return "Updated: unknown"

def _health_row(path_rel: str, label: str):
    c1, c2, c3 = st.columns([4,2,2])
    with c1: st.caption(f"{label} — {_human_lastmod(path_rel)}")
    ru = raw_url(path_rel); gu = github_page_url(path_rel)
    with c2:
        if ru: st.link_button("Open CSV (raw)", ru, use_container_width=True)
    with c3:
        if gu: st.link_button("Open on GitHub", gu, use_container_width=True)

def render_region(region: str) -> None:
    region = region.upper()
    st.subheader(f"{region} Index Dashboard")

    # Data health banners + open buttons
    indices_rel = f"data/snapshots/{region.lower()}_indices.csv"
    _health_row(indices_rel, "Indices snapshot")

    # Load snapshot
    df = load_csv_auto(indices_rel)

    # Choose default focus symbol
    focus_default = "SPY" if region == "NA" else ("VGK" if region == "EU" else "EWJ")
    if not df.empty and "symbol" in df.columns and pd.notna(df.iloc[0]["symbol"]):
        focus_default = str(df.iloc[0]["symbol"])

    # Region-specific focus key
    focus_key = f"focus_symbol_{region}"
    st.session_state.setdefault(focus_key, focus_default)
    render_focus(st.session_state[focus_key])

    if df.empty:
        st.info("No snapshot data yet. The hourly pipeline will populate CSVs.")
        return

    # Compact row fields
    if "rs" in df.columns:
        df["rs_flag"] = df["rs"].apply(_rs_flag)
    else:
        df["rs_flag"] = "•"
    df["trend"] = df.apply(_trend_row, axis=1)
    df["decision"] = df.get("decision","🟡 Wait")
    if "decision" in df.columns:
        df["decision"] = df["decision"].fillna("🟡 Wait")

    st.write("### Index Scorecard")
    for _, r in df.iterrows():
        sym = str(r.get("symbol", "")).strip()
        cols = st.columns([2, 1, 1, 1, 2, 2])
        with cols[0]:
            st.markdown(f"[**{sym}** ↗]({tv_symbol_url(sym)})", unsafe_allow_html=True)
        with cols[1]: st.write(r.get("price","—"))
        with cols[2]: st.write(r.get("chg_1d","—"))
        with cols[3]: st.write(r.get("rs_flag","•"))
        with cols[4]: st.write(r.get("trend","—"))
        with cols[5]: st.write(r.get("decision","🟡 Wait"))

        with st.expander(f"Details — {sym}"):
            details = {
                "Reasons": _reason_chips(r),
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
            }
            st.write(details)
            if st.button(f"Preview {sym} in Focus", key=f"focus_{region}_{sym}"):
                st.session_state[focus_key] = sym
                st.rerun()

    # Sector movers
    st.write("### Sector Movers")
    sectors_rel = f"data/snapshots/{region.lower()}_sectors.csv"
    _health_row(sectors_rel, "Sectors snapshot")
    sec = load_csv_auto(sectors_rel)
    if not sec.empty:
        st.dataframe(sec, use_container_width=True, hide_index=True)
    else:
        st.caption("No sector snapshot yet.")

    # FX & Commodities
    st.write("### FX & Commodities")
    fx_rel = f"data/snapshots/{region.lower()}_fxcmd.csv"
    _health_row(fx_rel, "FX/Commodities snapshot")
    fx = load_csv_auto(fx_rel)
    if not fx.empty:
        fx = fx.copy()
        fx["link"] = fx["symbol"].apply(tv_symbol_url)
        fx["symbol"] = fx.apply(lambda x: f"[{x['symbol']}]({x['link']})", axis=1)
        fx = fx.drop(columns=["link"])
        st.markdown(fx.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.caption("No FX/commodities snapshot yet.")

    # Daily report
    st.write("### Daily Report")
    report_rel = f"reports/{region}/latest.md"
    _health_row(report_rel, "Region report")
    rp = Path(report_rel)
    report_text = None
    if rp.exists():
        report_text = rp.read_text()
    else:
        import requests
        repo = os.getenv("VEGA_REPO",""); branch = os.getenv("VEGA_DATA_BRANCH","")
        if repo and branch:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{report_rel}"
            try:
                resp = requests.get(url, timeout=10)
                if resp.ok:
                    report_text = resp.text
            except Exception:
                pass
    if report_text:
        st.markdown(report_text)
        st.download_button("⬇️ Download report (MD)", report_text, file_name=f"{region}_report.md", mime="text/markdown")
    else:
        st.caption("No report generated yet.")
