import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Charts & Heatmap (Bridge)")

with st.expander("Login Help", expanded=False):
    render_login_helper()

st.subheader("Chart")
c1, c2, c3, c4 = st.columns([2,1,1,1])
with c1:
    symbol = st.text_input("Symbol", value=st.session_state.get("symbol", "NYSE:RBC"), key="symbol")
with c2:
    interval = st.selectbox("Interval",
                            ["1","5","15","30","60","D","W","M"],
                            index=["1","5","15","30","60","D","W","M"].index(st.session_state.get("interval","D")),
                            key="interval")
with c3:
    theme = st.selectbox("Theme",
                         ["dark","light"],
                         index=["dark","light"].index(st.session_state.get("theme","dark")),
                         key="theme")
with c4:
    mode = st.selectbox("Mode",
                        ["tvjs","iframe"],
                        index=["tvjs","iframe"].index(st.session_state.get("mode","tvjs")),
                        key="mode",
                        help="tv.js loads built-ins; iframe shows your TradingView layout/session.")

st.caption("Overlays (built-ins only)")
choices = [
    "EMA 9","EMA 21","EMA 50","EMA 200",
    "Bollinger (20,2)","Ichimoku (9/26/52)",
    "MACD (12/26/9)","RSI (14)","OBV","ATR (14)"
]
default_sel = [
    "EMA 9","EMA 21","EMA 50","EMA 200",
    "Bollinger (20,2)","Ichimoku (9/26/52)",
    "MACD (12/26/9)","RSI (14)","OBV","ATR (14)"
]

# Multiselect wired to session_state so Reset can drive the UI too
ov = st.multiselect(
    "Select studies",
    choices,
    default=st.session_state.get("ov", default_sel if st.session_state.get("mode","tvjs") != "iframe" else []),
    key="ov"
)

_name_to_code = {"EMA 9":"e9","EMA 21":"e21","EMA 50":"e50","EMA 200":"e200",
                 "Bollinger (20,2)":"bb","Ichimoku (9/26/52)":"ichi",
                 "MACD (12/26/9)":"macd","RSI (14)":"rsi","OBV":"obv","ATR (14)":"atr"}
codes = [_name_to_code[i] for i in ov]

if mode == "iframe":
    st.info("If the chart looks 'logged-out': sign in on TradingView in a new tab, then click Refresh under the chart.")

# 🔄 Reset button — restores HA + EMAs + built-ins, and heatmap to USA
if st.button("Reset to Vega Defaults (HA + EMAs + Built-ins)"):
    st.session_state["symbol"] = "NYSE:RBC"   # you chose to keep a fixed ticker on reset
    st.session_state["interval"] = "D"
    st.session_state["theme"] = "dark"
    st.session_state["mode"] = "tvjs"
    st.session_state["ov"] = default_sel
    st.session_state["region"] = "USA"        # also reset heatmap region per your choice
    st.experimental_rerun()

render_chart(symbol, interval=interval, theme=theme,
             height=600, overlays=(codes if mode!='iframe' else None), mode=mode)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA","Canada","Mexico"],
                      index=["USA","Canada","Mexico"].index(st.session_state.get("region","USA")),
                      key="region")
render_heatmap(region, height=520)
