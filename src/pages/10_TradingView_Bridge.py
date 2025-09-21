
"""
src/pages/10_TradingView_Bridge.py — Super-sized NA-style chart
"""
import streamlit as st
from urllib.parse import urlencode
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView — Bridge", layout="wide")

# --- Compact CSS to kill dead space
st.markdown("""
<style>
.block-container{padding-top:.6rem;padding-bottom:.6rem}
section.main > div {gap:.6rem}
.stButton > button{width:100%}
</style>
""", unsafe_allow_html=True)

# --- Fullscreen route (no sidebar chrome)
qp = st.query_params
if qp.get("fullscreen", ["0"])[0] == "1":
    symbol = qp.get("symbol", ["NASDAQ:QQQ"])[0]
    interval = qp.get("interval", ["D"])[0]
    theme = qp.get("theme", ["dark"])[0]
    height = int(qp.get("height", ["1200"])[0])
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    st.stop()

st.title("TradingView — Bridge")

with st.sidebar:
    st.subheader("Chart controls")
    symbol = st.text_input("Symbol", "NASDAQ:QQQ")
    interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
    theme = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
    height = st.slider("Chart height", 600, 2000, 1200, 20)
    layout = st.radio("Layout", ["Chart only", "Chart + Heatmap"], index=0)

def _open_fullscreen(symbol, interval, theme, height):
    params = {"fullscreen":"1","symbol":symbol,"interval":interval,"theme":theme,"height":height}
    st.link_button("Open full-page chart (in-app)", f"?{urlencode(params)}", use_container_width=True)

# Top actions
_open_fullscreen(symbol, interval, theme, height)

# Chart section
st.subheader("Chart", anchor="chart")
if layout == "Chart only":
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
else:
    col1, col2 = st.columns([3,1])
    with col1:
        render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    with col2:
        hm_height = max(420, height-60)
        render_heatmap(market="US", theme=theme, height=hm_height)

with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
    render_login_helper("Public widgets for now. Height slider + full-page view enabled.")
