import os, pandas as pd, streamlit as st

st.set_page_config(page_title="North America — Text Dashboard v1.0", layout="wide")
st.title("North America — Text Dashboard v1.0")

MD_PATH = "reports/na/morning_report.md"
CAL_CSV = "assets/econ_calendar_na.csv"

st.subheader("Morning Report")
if os.path.isfile(MD_PATH):
    st.markdown(open(MD_PATH, "r", encoding="utf-8").read())
else:
    st.info("Morning report not found yet. It will appear after the next CI run commits it.")

st.subheader("Economic Calendar")
if os.path.isfile(CAL_CSV):
    df = pd.read_csv(CAL_CSV)
    q = st.text_input("Filter events (keyword/date/time/impact)").strip()
    if q:
        ql = q.lower()
        dfv = df[df.apply(lambda r: any(ql in str(v).lower() for v in r.values), axis=1)]
    else:
        dfv = df
    st.dataframe(dfv, use_container_width=True, hide_index=True)
else:
    st.info("Calendar CSV not found yet. It will appear after the next CI run.")
