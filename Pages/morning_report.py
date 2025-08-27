from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from styling import pill, color_dot, color_block

@dataclass
class MorningReport:
    provider: Any
    regions: List[str]
    session_date: date

    # ---------- Section 1: Macro Header ----------
    def render_macro_header(self):
        meta = self.provider.get_macro_snapshot()
        st.markdown(f"### North America Morning Report — {self.session_date.strftime('%a %b %d, %Y')}")
        st.write(
            f"**Tone:** {meta['tone']}  "
            f"{pill('USD ' + meta['usd'], meta['usd'])} "
            f"{pill('Gold ' + meta['gold'], meta['gold'])} "
            f"{pill('Oil ' + meta['oil'], meta['oil'])} "
            f"{pill('Rates ' + meta['rates'], meta['rates'])} "
            f"{pill('VIX ' + meta['vix'], meta['vix'])}"
        )
        cols = st.columns(4)
        cols[0].metric("SPY", meta['indices']['SPY']['level'], meta['indices']['SPY']['pct'])
        cols[1].metric("QQQ", meta['indices']['QQQ']['level'], meta['indices']['QQQ']['pct'])
        cols[2].metric("IWM", meta['indices']['IWM']['level'], meta['indices']['IWM']['pct'])
        cols[3].metric("VIX", meta['vix_level'], meta['vix_chg'])

        st.caption("Tip: levels auto-refresh when wired to your live provider.")

    # ---------- Section 2: Benchmark & Breadth Matrix (daily must-have) ----------
    def render_benchmark_and_breadth_matrix(self):
        data = self.provider.get_benchmark_and_breadth()
        st.markdown("## 📊 Benchmark & Breadth Matrix")
        df = pd.DataFrame(data['benchmarks']).set_index("Index")
        st.dataframe(df, use_container_width=True)

        st.markdown("### Sector Breadth Matrix")
        sdf = pd.DataFrame(data['sectors']).set_index("Sector")
        st.dataframe(sdf, use_container_width=True)

        st.info(
            "Takeaway: "
            + data['takeaway']
        )

    # ---------- Section 3: Options & Skews (optional) ----------
    def render_options_and_skews(self):
        d = self.provider.get_options_skews()
        st.markdown("## 🧮 Options Flow & Skews")
        for row in d:
            c = st.container()
            with c:
                st.write(
                    f"**{row['ticker']}** — IVR {row['ivr']}; skew: {row['skew']} → "
                    f"**Plan:** {row['plan']}"
                )

    # ---------- Section 4: Catalyst Board (optional) ----------
    def render_catalyst_board(self):
        st.markdown("## 📰 Single-Stock & Sector Catalyst Board")
        items = self.provider.get_catalyst_board()
        for it in items:
            with st.expander(f"{it['title']} — {it['summary']}"):
                st.write(it['details'])
                st.write(f"**Plan:** {it['plan']}")

    # ---------- Section 5: Session Map (daily must-have) ----------
    def render_session_map(self):
        smap = self.provider.get_session_map()
        st.markdown("## 🗺️ Session Map (Roadmap for Today)")
        for item in smap:
            st.markdown(f"- **{item['window']}**: {item['text']}")

    # ---------- Section 6: VectorVest Alt Color Guard (daily must-have) ----------
    def render_color_guard_alt(self):
        st.markdown("## 🟩🟨🟥 VectorVest-Style Color Guard (Alt)")
        cg = self.provider.get_color_guard_inputs()

        # Signals: Price Trend, Breadth Trend, Risk/VIX
        grid = st.columns(3)
        grid[0].markdown(self._cg_light("Price Trend", cg['price_signal']))
        grid[1].markdown(self._cg_light("Breadth Trend", cg['breadth_signal']))
        grid[2].markdown(self._cg_light("Risk / VIX", cg['risk_signal']))

        st.caption(
            "Green = favorable; Yellow = neutral/choppy; Red = risk-off. "
            "Lights are computed from SPY trend vs VWAP/PDH, NYSE breadth %, and VIX thresholds."
        )

    def _cg_light(self, label: str, state: str) -> str:
        color = {"green": "#16a34a", "yellow": "#f59e0b", "red": "#dc2626"}[state]
        return color_block(label, color)

    # ---------- Section 7: Final Risk Overlay (daily must-have) ----------
    def render_final_risk_overlay(self):
        fr = self.provider.get_final_risk_overlay()
        st.markdown("## 🛡️ Final Risk Overlay & Action Plan")
        st.markdown("### Hedge Triggers")
        st.markdown(f"- Primary: {fr['primary']}")
        st.markdown(f"- Secondary: {fr['secondary']}")

        st.markdown("### FX Guardrails")
        st.markdown(f"- {fr['fx']}")

        st.markdown("### Tactical Implications")
        for t in fr['tactical']:
            st.markdown(f"- {t}")

        st.markdown("### Trade Now vs Wait")
        tdf = pd.DataFrame(fr['trade_board'])
        st.dataframe(tdf, use_container_width=True)
