import os, json, pandas as pd, datetime as dt
import streamlit as st
from streamlit.components.v1 import html
from urllib.parse import quote

st.set_page_config(page_title="Europe — Text Dashboard v1.5", layout="wide")
st.title("Europe — Text Dashboard v1.5")

MD_PATH = "reports/eu/morning_report.md"
CAL_CSV = "assets/econ_calendar_europe.csv"
META    = "reports/run_meta.json"

# --- Cached CSV loader ---
@st.cache_data(show_spinner=False)
def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def _mtime(path: str) -> str:
    try:
        ts = os.path.getmtime(path)
        return dt.datetime.fromtimestamp(ts).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return "—"

def _load_meta():
    try:
        return json.load(open(META, "r", encoding="utf-8"))
    except Exception:
        return {}

def tv_chart_html(symbol: str, interval: str, theme: str, height: int,
                  studies: list, studies_overrides: dict | None) -> str:
    cfg = {
        "symbol": symbol, "interval": interval, "timezone": "Etc/UTC",
        "theme": theme, "style": "1", "locale":"en",
        "studies": studies,
        "allow_symbol_change": True, "withdateranges": True, "details": True, "calendar": True,
        "autosize": True, "container_id": "tv_quick_eu"
    }
    if studies_overrides:
        cfg["studies_overrides"] = studies_overrides
    return f"""
<div id="tv_quick_eu" style="height:{height}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script> new TradingView.widget({json.dumps(cfg)}); </script>
"""

# Quick Chart (TOP, CENTERED)
st.subheader("Quick Chart")

PANE_STUDIES = [
    "RSI@tv-basicstudies","MACD@tv-basicstudies",
    "ATR@tv-basicstudies","OBV@tv-basicstudies","Volume@tv-basicstudies"
]
OVERLAY_CHOICES = {
    "EMA 9":   ("MAExp@tv-basicstudies", 9),
    "EMA 21":  ("MAExp@tv-basicstudies", 21),
    "EMA 50":  ("MAExp@tv-basicstudies", 50),
    "EMA 200": ("MAExp@tv-basicstudies", 200),
    "Bollinger (20,2)": ("BollingerBands@tv-basicstudies", None),
    "Ichimoku (9/26/52)": ("IchimokuCloud@tv-basicstudies", None),
}
overlay_default = ["EMA 9", "EMA 21", "EMA 50", "EMA 200"]
ema_order = ["EMA 9","EMA 21","EMA 50","EMA 200"]

EU_LIST = ["NYSEARCA:VGK","NYSEARCA:EZU","NYSEARCA:FEZ","TVC:FTSE"]

cc1, cc2, cc3, cc4 = st.columns([2,1,1,1])
symbol  = cc1.selectbox("Symbol", EU_LIST, index=0)
interval = cc2.selectbox("Interval", ["1","5","15","60","240","D","W","M"], index=5)
theme    = cc3.selectbox("Theme", ["light","dark"], index=1)
height   = cc4.slider("Height", 480, 1200, 800, step=20)

# overlays picker with Reset
if "eu_overlays" not in st.session_state:
    st.session_state["eu_overlays"] = overlay_default
sel_overlays = st.multiselect("Overlays", list(OVERLAY_CHOICES.keys()),
                              default=st.session_state["eu_overlays"],
                              key="eu_overlays")
col_reset, _ = st.columns([1,5])
with col_reset:
    if st.button("Reset EMAs", key="eu_reset"):
        st.session_state["eu_overlays"] = overlay_default
        st.rerun()

ordered = [k for k in ema_order if k in sel_overlays] + [k for k in sel_overlays if k not in ema_order]
overlay_studies, ema_lengths = [], []
for name in ordered:
    study, length = OVERLAY_CHOICES[name]
    overlay_studies.append(study)
    if study == "MAExp@tv-basicstudies" and isinstance(length, int):
        ema_lengths.append(length)
studies = overlay_studies + PANE_STUDIES
studies_overrides = {f"MAExp@tv-basicstudies.{i}.length": ln for i, ln in enumerate(ema_lengths)}

manual = st.text_input("Or type a TV symbol (e.g., NYSEARCA:VGK)", "").strip()
if manual:
    symbol = manual

l, m, r = st.columns([1,8,1])
with m:
    html(tv_chart_html(symbol, interval, theme, height, studies, studies_overrides),
         height=height+20, scrolling=False)
with m:
    params = f"?symbol={quote(symbol)}&interval={interval}&theme={theme}&height={height}"
    st.link_button("Open full-page chart (in-app)", f"/TradingView_Charts{params}")
    st.markdown(f"[Open on TradingView](https://www.tradingview.com/chart/?symbol={quote(symbol)}&interval={interval})  •  [Share this preset]({params})")

# Morning Report
st.subheader("Morning Report")
if os.path.isfile(MD_PATH):
    st.markdown(open(MD_PATH, "r", encoding="utf-8").read())
    st.caption(f"Last updated: { _mtime(MD_PATH) }")
else:
    st.info("Morning report not found yet. It will appear after the next CI run commits it.")

# Economic Calendar
st.subheader("Economic Calendar")
if os.path.isfile(CAL_CSV):
    df = _read_csv(CAL_CSV)
    for col in ("date","time_tz","region","event","impact"):
        if col not in df.columns: df[col] = ""

    c1, c2 = st.columns([2,1])
    q = c1.text_input("Filter (keyword/date/time/impact)").strip()
    impacts = sorted([x for x in df["impact"].dropna().unique().tolist() if str(x).strip() != ""])
    sel = c2.multiselect("Impact", options=impacts, default=impacts)

    dfv = df.copy()
    if sel: dfv = dfv[dfv["impact"].isin(sel)]
    if q:
        ql = q.lower()
        dfv = dfv[dfv.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]

    if not dfv.empty:
        for d, grp in dfv.groupby("date"):
            with st.expander(f"{d} ({len(grp)})", expanded=True):
                st.dataframe(grp.reset_index(drop=True), use_container_width=True, hide_index=True)
    else:
        st.info("No rows match your filters.")

    st.download_button("Download filtered CSV",
        dfv.to_csv(index=False).encode("utf-8"),
        file_name="econ_calendar_eu_filtered.csv", mime="text/csv")

    def to_ics(df_):
        lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Vega//Calendar//EN"]
        now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for _, r in df_.iterrows():
            date_str = str(r.get("date","")).strip()
            time_str = str(r.get("time_tz","")).strip()
            summary = f"{r.get('event','')}".replace("\n"," ")
            impact  = str(r.get("impact","")).strip()
            desc = f"Region: {r.get('region','')}; Time: {time_str}; Impact: {impact}"

            dt_val = pd.to_datetime(f"{date_str} {time_str}", errors="coerce")
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{date_str}-{abs(hash(summary))}@vega")
            lines.append(f"DTSTAMP:{now}")
            if pd.isna(dt_val):
                ymd = pd.to_datetime(date_str, errors="coerce")
                if pd.isna(ymd):
                    lines.append(f"SUMMARY:{summary}")
                else:
                    lines.append(f"DTSTART;VALUE=DATE:{ymd.strftime('%Y%m%d')}")
                    lines.append(f"SUMMARY:{summary}")
            else:
                lines.append(f"DTSTART:{dt_val.strftime('%Y%m%dT%H%M%S')}")
                lines.append(f"SUMMARY:{summary}")
            lines.append(f"DESCRIPTION:{desc}")
            lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines).encode("utf-8")

    st.download_button("Download filtered .ics", to_ics(dfv),
        file_name="econ_calendar_eu_filtered.ics", mime="text/calendar")
else:
    st.info("Calendar CSV not found yet. It will appear after the next CI run commits it.")

meta = _load_meta()
if meta:
    st.caption(f"Pipeline run: [{meta.get('run_id','')}]({meta.get('run_url','')}) • UTC: {meta.get('timestamp_utc','')}")
