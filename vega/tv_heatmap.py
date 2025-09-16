import streamlit as st
from .tradingview import heatmap_for_country, screener_for_country

def render(countries, show_screener: bool=False):
    st.markdown("#### Sector Heatmaps")
    cols = st.columns(len(countries) if countries else 1)
    for i, c in enumerate(countries or []):
        with cols[i % max(1, len(cols))]:
            st.caption(c)
            heatmap_for_country(c)
    if show_screener and countries:
        st.markdown("---")
        st.markdown("#### Screener")
        for c in countries:
            st.markdown(f"**{c}**")
            screener_for_country(c, height=600)
