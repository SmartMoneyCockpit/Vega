import os, pandas as pd, streamlit as st, datetime as dt

st.set_page_config(page_title="APAC — Text Dashboard v1.1", layout="wide")
st.title("APAC — Text Dashboard v1.1")

MD_PATH = "reports/apac/morning_report.md"
CAL_CSV = "assets/econ_calendar_apac.csv"
META    = "reports/run_meta.json"

def _mtime(path: str) -> str:
    try:
        ts = os.path.getmtime(path)
        return dt.datetime.fromtimestamp(ts).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return "—"

def _load_meta():
    try:
        import json
        return json.load(open(META, "r", encoding="utf-8"))
    except Exception:
        return {}

st.subheader("Morning Report")
if os.path.isfile(MD_PATH):
    st.markdown(open(MD_PATH, "r", encoding="utf-8").read())
    st.caption(f"Last updated: { _mtime(MD_PATH) }")
else:
    st.info("Morning report not found yet. It will appear after the next CI run commits it.")

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
    if sel:
        dfv = dfv[dfv["impact"].isin(sel)]
    if q:
        ql = q.lower()
        dfv = dfv[dfv.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]

    if not dfv.empty:
        for d, grp in dfv.groupby("date"):
            with st.expander(f"{d} ({len(grp)})", expanded=True):
                st.dataframe(grp.reset_index(drop=True), use_container_width=True, hide_index=True)
    else:
        st.info("No rows match your filters.")

    st.download_button("Download filtered CSV", dfv.to_csv(index=False).encode("utf-8"),
                       file_name="econ_calendar_apac_filtered.csv", mime="text/csv")

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
            lines += [
                "BEGIN:VEVENT","UID:"+uid,"DTSTAMP:"+now,
                "DTSTART;VALUE=DATE:"+ymd,
                "SUMMARY:"+summary + (f" ({impact})" if impact else ""),
                "DESCRIPTION:"+desc,
                "END:VEVENT"
            ]
        lines += ["END:VCALENDAR"]
        return "\r\n".join(lines).encode("utf-8")

    st.download_button("Download filtered .ics", to_ics(dfv), file_name="econ_calendar_apac_filtered.ics",
                       mime="text/calendar")
else:
    st.info("Calendar CSV not found yet. It will appear after the next CI run.")

meta = _load_meta()
if meta:
    st.caption(f"Pipeline run: [{meta.get('run_id','')}]({meta.get('run_url','')}) • "
               f"UTC: {meta.get('timestamp_utc','')}")
