import os, json, pandas as pd, datetime as dt
import streamlit as st
from streamlit.components.v1 import html
from urllib.parse import quote

st.set_page_config(page_title="Europe — Text Dashboard v1.6", layout="wide")
st.title("Europe — Text Dashboard v1.6")

MD_PATH = "reports/eu/morning_report.md"
CAL_CSV = "assets/econ_calendar_europe.csv"
META    = "reports/run_meta.json"

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

def _get_qp() -> dict:
    try:
        qp = st.query_params
        out = {}
        for k, v in qp.items():
            if isinstance(v, list): out[k] = v[0] if v else ""
            else: out[k] = v
        return out
    except Exception:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) and v else "") for k, v in qp.items()}

def _qp_get(name: str, default: str) -> str:
    v = _get_qp().get(name, default)
    if name == "height":
        try: return str(int(v))
        except: return str(default)
    return v or default

OVERLAY_CODES = {
    "EMA 9":"e9", "EMA 21":"e21", "EMA 50":"e50", "EMA 200":"e200",
    "Bollinger (20,2)":"bb", "Ichimoku (9/26/52)":"ichi",
}
CODE_TO_OVERLAY = {v:k for k,v in OVERLAY_CODES.items()}
EMA_ORDER = ["EMA 9","EMA 21","EMA 50","EMA 200"]

def _decode_overlays(code_csv: str, default: list[str]) -> list[str]:
    if not code_csv: return default
    parts = [p.strip() for p in code_csv.split(",") if p.strip()]
    names = [CODE_TO_OVERLAY.get(p) for p in parts if CODE_TO_OVERLAY.get(p)]
    return names or default

def _encode_overlays(names: list[str]) -> str:
    ordered = [n for n in EMA_ORDER if n in names] + [n for n in names if n not in EMA_ORDER]
    return ",".join(OVERLAY_CODES[n] for n in ordered if n in OVERLAY_CODES)

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
OVERLAY_DEFAULT = ["EMA 9","EMA 21","EMA 50","EMA 200"]

EU_LIST = ["NYSEARCA:VGK","NYSEARCA:EZU","NYSEARCA:FEZ","TVC:FTSE"]

qp = _get_qp()
symbol_qp   = qp.get("symbol", EU_LIST[0])
interval_qp = qp.get("interval", "D")
theme_qp    = qp.get("theme", "dark")
height_qp   = int(_qp_get("height", "800"))
ov_qp       = _decode_overlays(qp.get("ov",""), OVERLAY_DEFAULT)

cc1, cc2, cc3, cc4 = st.columns([2,1,1,1])
symbol  = cc1.selectbox("Symbol", EU_LIST, index=(EU_LIST.index(symbol_qp) if symbol_qp in EU_LIST else 0))
interval = cc2.selectbox("Interval", ["1","5","15","60","240","D","W","M"],
                         index=["1","5","15","60","240","D","W","M"].index(interval_qp) if interval_qp in ["1","5","15","60","240","D","W","M"] else 5)
theme    = cc3.selectbox("Theme", ["light","dark"], index=(0 if theme_qp=="light" else 1))
height   = cc4.slider("Height", 480, 1200, height_qp, step=20)

if "eu_overlays" not in st.session_state:
    st.session_state["eu_overlays"] = ov_qp
sel_overlays = st.multiselect("Overlays", list(OVERLAY_CHOICES.keys()),
                              default=st.session_state["eu_overlays"],
                              key="eu_overlays")
if st.button("Reset EMAs", key="eu_reset"):
    st.session_state["eu_overlays"] = OVERLAY_DEFAULT
    st.rerun()

ordered = [n for n in EMA_ORDER if n in sel_overlays] + [n for n in sel_overlays if n not in EMA_ORDER]
overlay_studies, ema_lengths = [], []
for name in ordered:
    study, length = OVERLAY_CHOICES[name]
    overlay_studies.append(study)
    if study == "MAExp@tv-basicstudies" and isinstance(length, int):
        ema_lengths.append(length)
studies = overlay_studies + PANE_STUDIES
studies_overrides = {f"MAExp@tv-basicstudies.{i}.length": ln for i, ln in enumerate(ema_lengths)}

manual = st.text_input("Or type a TV symbol (e.g., NYSEARCA:VGK)", "").strip()
if manual: symbol = manual

l, m, r = st.columns([1,8,1])
with m:
    html(tv_chart_html(symbol, interval, theme, height, studies, studies_overrides),
         height=height+20, scrolling=False)
with m:
    ov_param = ",".join(OVERLAY_CODES[n] for n in ordered if n in OVERLAY_CODES)
    params = f"?symbol={quote(symbol)}&interval={interval}&theme={theme}&height={height}&ov={ov_param}"
    st.link_button("Open full-page chart (in-app)", f"/TradingView_Charts{params}")
    st.markdown(f"[Open on TradingView](https://www.tradingview.com/chart/?symbol={quote(symbol)}&interval={interval})")
    st.text_input("Copy dashboard link", value=params, label_visibility="visible")

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

    IMPACT_MAP = {"High":"🔴 High","Medium":"🟠 Medium","Med":"🟠 Medium","Low":"🟢 Low","-":"⚪ None","None":"⚪ None","":"⚪ None"}
    if "impact" in df.columns:
        df["impact"] = df["impact"].map(lambda x: IMPACT_MAP.get(str(x).strip(), str(x)))
    cols = [c for c in ["date","time_tz","region","event","impact"] if c in df.columns]
    if cols: df = df[cols + [c for c in df.columns if c not in cols]]

    c1, c2 = st.columns([2,1])
    q = c1.text_input("Filter (keyword/date/time/impact)").strip()
    impacts = sorted(set(v for v in df.get("impact", pd.Series(dtype=str)).dropna().tolist() if str(v).strip()))
    sel = c2.multiselect("Impact", options=impacts, default=impacts)

    dfv = df.copy()
    if "impact" in dfv and sel: dfv = dfv[dfv["impact"].isin(sel)]
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
            lines += ["BEGIN:VEVENT", f"UID:{date_str}-{abs(hash(summary))}@vega", f"DTSTAMP:{now}"]
            if pd.isna(dt_val):
                ymd = pd.to_datetime(date_str, errors="coerce")
                if pd.isna(ymd):
                    lines += [f"SUMMARY:{summary}"]
                else:
                    lines += [f"DTSTART;VALUE=DATE:{ymd.strftime('%Y%m%d')}", f"SUMMARY:{summary}"]
            else:
                lines += [f"DTSTART:{dt_val.strftime('%Y%m%dT%H%M%S')}", f"SUMMARY:{summary}"]
            lines += [f"DESCRIPTION:{desc}", "END:VEVENT"]
        lines += ["END:VCALENDAR"]
        return "\r\n".join(lines).encode("utf-8")

    st.download_button("Download filtered .ics", to_ics(dfv),
        file_name="econ_calendar_eu_filtered.ics", mime="text/calendar")
else:
    st.info("Calendar CSV not found yet. It will appear after the next CI run commits it.")

meta = _load_meta()
if meta:
    st.caption(f"Pipeline run: [{meta.get('run_id','')}]({meta.get('run_url','')}) • UTC: {meta.get('timestamp_utc','')}")
