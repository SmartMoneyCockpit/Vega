import streamlit as st, pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from app_auth import login_gate
if not login_gate(): pass
from data_bridge import get_rs_df
import db_adapter as db

st.set_page_config(page_title='RS Dashboard', layout='wide')
st.title('Relative Strength Momentum Dashboard')

today=date.today(); default_start=today - timedelta(weeks=26)
colc=st.columns([2,2,2,2])
with colc[0]:
    buckets = get_rs_df()['Bucket'].unique().tolist()
    selected = st.multiselect('Buckets', buckets, default=buckets[:4])
with colc[1]:
    start = st.date_input('Start', default_start)
with colc[2]:
    end = st.date_input('End', today)

st.subheader('Current RS Snapshot')
st.dataframe(get_rs_df(), use_container_width=True)

st.subheader('RS Trends (26‑week)')
hist = db.load_rs_history(selected or None, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
if hist.empty:
    st.info('No RS history yet. It will populate after the daily export runs.')
else:
    for b in (selected or buckets):
        sub = hist[hist['Bucket']==b]
        if sub.empty: continue
        fig, ax = plt.subplots()
        ax.plot(pd.to_datetime(sub['dt']), sub['Value'])
        ax.set_title(f"{b} — RS Value (🟢1.4, 🟠1.2, 🟡1.0, 🔴0.8)")
        ax.set_xlabel('Date'); ax.set_ylabel('RS Value')
        st.pyplot(fig)
