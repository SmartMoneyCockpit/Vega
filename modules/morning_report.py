from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import streamlit as st, pandas as pd
from typing import List, Any
from .styling import pill, color_block

@dataclass
class MorningReport:
    provider: Any
    regions: List[str]
    session_date: date

    def render_macro_header(self):
        m = self.provider.get_macro_snapshot()
        st.markdown(f"### North America Morning Report — {self.session_date.strftime('%a %b %d, %Y')}")
        st.write(
            f"**Tone:** {m['tone']}  "
            f"{pill('USD ' + m['usd'], m['usd'])} "
            f"{pill('Gold ' + m['gold'], m['gold'])} "
            f"{pill('Oil ' + m['oil'], m['oil'])} "
            f"{pill('Rates ' + m['rates'], m['rates'])} "
            f"{pill('VIX ' + m['vix'], m['vix'])}",
            unsafe_allow_html=True
        )
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("SPY", m['indices']['SPY']['level'], m['indices']['SPY']['pct'])
        c2.metric("QQQ", m['indices']['QQQ']['level'], m['indices']['QQQ']['pct'])
        c3.metric("IWM", m['indices']['IWM']['level'], m['indices']['IWM']['pct'])
        c4.metric("VIX", m['vix_level'], m['vix_chg'])

    def render_benchmark_and_breadth_matrix(self):
        d = self.provider.get_benchmark_and_breadth()
        st.markdown("## 📊 Benchmark & Breadth Matrix")
        st.dataframe(pd.DataFrame(d['benchmarks']).set_index("Index"), use_container_width=True)
        st.markdown("### Sector Breadth Matrix")
        st.dataframe(pd.DataFrame(d['sectors']).set_index("Sector"), use_container_width=True)
        st.info("Takeaway: " + d['takeaway'])

    def render_options_and_skews(self):
        st.markdown("## 🧮 Options Flow & Skews")
        for r in self.provider.get_options_skews():
            st.write(f"**{r['ticker']}** — IVR {r['ivr']}; skew: {r['skew']} → **Plan:** {r['plan']}")

    def render_catalyst_board(self):
        st.markdown("## 📰 Single-Stock & Sector Catalyst Board")
        for it in self.provider.get_catalyst_board():
            with st.expander(f"{it['title']} — {it['summary']}"):
                st.write(it['details'])
                st.write(f"**Plan:** {it['plan']}")

    def render_session_map(self):
        st.markdown("## 🗺️ Session Map (Roadmap for Today)")
        for i in self.provider.get_session_map():
            st.markdown(f"- **{i['window']}**: {i['text']}")

    def render_color_guard_alt(self):
        st.markdown("## 🟩🟨🟥 VectorVest-Style Color Guard (Alt)")
        cg = self.provider.get_color_guard_inputs()
        a,b,c = st.columns(3)
        a.markdown(color_block("Price Trend", {"green":"#16a34a","yellow":"#f59e0b","red":"#dc2626"}[cg['price_signal']]), unsafe_allow_html=True)
        b.markdown(color_block("Breadth Trend", {"green":"#16a34a","yellow":"#f59e0b","red":"#dc2626"}[cg['breadth_signal']]), unsafe_allow_html=True)
        c.markdown(color_block("Risk / VIX", {"green":"#16a34a","yellow":"#f59e0b","red":"#dc2626"}[cg['risk_signal']]), unsafe_allow_html=True)
        st.caption("Green=favorable · Yellow=neutral/choppy · Red=risk-off.")

    def render_final_risk_overlay(self):
        fr = self.provider.get_final_risk_overlay()
        st.markdown("## 🛡️ Final Risk Overlay & Action Plan")
        st.markdown("### Hedge Triggers"); st.markdown(f"- Primary: {fr['primary']}"); st.markdown(f"- Secondary: {fr['secondary']}")
        st.markdown("### FX Guardrails"); st.markdown(f"- {fr['fx']}")
        st.markdown("### Tactical Implications"); [st.markdown(f"- {t}") for t in fr['tactical']]
        st.markdown("### Trade Now vs Wait"); st.dataframe(pd.DataFrame(fr['trade_board']), use_container_width=True)
