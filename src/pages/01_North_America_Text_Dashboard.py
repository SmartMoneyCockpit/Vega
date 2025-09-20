import os, json, pandas as pd, datetime as dt
import streamlit as st
from streamlit.components.v1 import html
from urllib.parse import quote

st.set_page_config(page_title="North America — Text Dashboard v1.3", layout="wide")
st.title("North America — Text Dashboard v1.3")

MD_PATH = "reports/na/morning_report.md"
CAL_CSV = "assets/econ_calendar_na.csv"
META    = "reports/run_meta.json"

# ---------------- Helpers ----------------
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

def tv_chart_html(symbol: str, interval: str="D", theme: str="light", height: int=640) -> str:
    cfg = {
        "symbol": symbol,
        "interval": interval,
        "timezone": "Etc/UTC",
        "theme": theme,
        "style": "1",
        "locale": "en",
        "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies", "MAExp@tv-basicstudies"],
        "allow_symbol_change": True,
        "withdateranges": True,
        "details": True,
        "calendar": True,
        "autosize": True,
        "container_id": "tv_na_chart"
    }
    return f"""
<div id="tv_na_chart" style="height:{height}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script> new TradingView.widget({json.dumps(cfg)}); </script>
"""

# ---------------- Quick Chart (TOP, CENTERED) ----------------
st.subheader("Quick Chart")
NA_LIST = ["NYSEARCA:SPY","NASDAQ:QQQ","NYSEARCA:DIA","NYSEARCA:IWM","CBOE:VIX"]

cc1, cc2, cc3, cc4 = st.columns([2,1,1,1])
symbol  = cc1.selectbox("Symbol", NA_LIST, index=0)
interval = cc2.selectbox("Interval", ["1","5","15","60","240","D","W","M"], index=5)
theme    = cc3.selectbox("Theme", ["light","dark"], index=1)
height   = cc4.slider("Height", 480, 1200, 720, step=20)

manual = st.text_input("Or type a TV symbol (e.g., NYSEARCA:SPY)", "").strip()
if manual:
    symbol = manual

# Center the chart (narrow side columns, wide center column)
left, mid, right = st.columns([1, 8, 1])
with mid:
    html(tv_chart_html(symbol, interval, theme, height=height), height=height+20, scrolling=False)

# Pop-out actions
pop_left, pop_mid, pop_right = st.columns([1,8,1])
with pop_mid:
    st.link_button("Open full-page chart (in-app)", "/TradingView_Charts")
    st.markdown(
        f"[Open on TradingView]("
        f"https://www.tradingview.com/chart/?symbol={quote(symbol)}&interval={interval}"
        f")"
    )

# ---------------- Morning Report ----------------
st.subheader("Morning Report")
if os.path.isfile(MD_PATH):
    st.markdown(open(MD_PATH, "r", encoding="utf-8").read())
    st.caption(f"Last updated: { _mtime(MD_PATH) }")
else:
    st.info("Morning report not found yet. It will appear after the next CI run commits it.")

# ---------------- Economic Calendar ----------------
st.subheader("Economic Calendar")
if os.path.isfile(CAL_CSV):
    df = pd.read_csv(CAL_CSV)
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
        file_name="econ_calendar_na_filtered.csv", mime="text/csv")

    def to_ics(df_):
        lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Vega//Calendar//EN"]
        now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for _, r in df_.iterrows():
            date = pd.to_datetime(str(r.get("date","")), errors="coerce")
            if pd.isna(date): continue
            ymd = date.strftime("%Y%m%d")
            summary = f"{r.get('event','')}".replace("\n"," ")
            impact  = str(r.get("impact","")).strip()
            desc = f"Region: {r.get('region','')}; Time: {r.get('time_tz','')}; Impact: {impact}"
            uid = f"{ymd}-{abs(hash(summary))}@vega"
            lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{now}",
                      f"DTSTART;VALUE=DATE:{ymd}",
                      f"SUMMARY:{summary}" + (f" ({impact})" if impact else ""),
                      f"DESCRIPTION:{desc}", "END:VEVENT"]
        lines += ["END:VCALENDAR"]
        return "\r\n".join(lines).encode("utf-8")

    st.download_button("Download filtered .ics", to_ics(dfv),
        file_name="econ_calendar_na_filtered.ics", mime="text/calendar")
else:
    st.info("Calendar CSV not found yet. It will appear after the next CI run.")

meta = _load_meta()
if meta:
    st.caption(f"Pipeline run: [{meta.get('run_id','')}]({meta.get('run_url','')}) • UTC: {meta.get('timestamp_utc','')}")
