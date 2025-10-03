import streamlit as st, pandas as pd, numpy as np, os, io, zipfile
from datetime import datetime, timezone
from app_auth import login_gate
if not login_gate(): pass
from data_bridge import get_positions_df, get_signals_df, get_breadth_df, get_rs_df
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except Exception: REPORTLAB_AVAILABLE = False

st.set_page_config(page_title='Owner\'s Daily Digest', layout='wide')
st.title("Owner's Daily Digest – 1‑Pager & CSV Pack")

@st.cache_data(show_spinner=False)
def _now(): return datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')
def _ensure(path): os.makedirs(path, exist_ok=True); return path

pos = get_positions_df(); sig = get_signals_df(); br = get_breadth_df(); rs = get_rs_df()
l, r = st.columns([3,2])
with l:
    st.markdown('**Positions**'); st.dataframe(pos, use_container_width=True)
    st.markdown('**Signals**'); st.dataframe(sig, use_container_width=True)
with r:
    st.markdown('**Breadth**'); st.dataframe(br, use_container_width=True)
    st.markdown('**Relative Strength**'); st.dataframe(rs, use_container_width=True)
st.divider()

def build_zip(p,s,b,r):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('positions.csv', p.to_csv(index=False))
        z.writestr('signals.csv', s.to_csv(index=False))
        z.writestr('breadth.csv', b.to_csv(index=False))
        z.writestr('relative_strength.csv', r.to_csv(index=False))
    buf.seek(0); return buf.read()

def build_pdf(p,s,b,r):
    if not REPORTLAB_AVAILABLE: raise RuntimeError('reportlab not installed')
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); W,H=A4
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.setFont('Helvetica-Bold', 16); c.drawString(20*mm, H-20*mm, "Owner's Daily Digest")
    c.setFont('Helvetica', 9); c.drawString(20*mm, H-26*mm, f'Generated: {ts}'); y = H-36*mm
    def section(t): 
        nonlocal y; c.setFont('Helvetica-Bold',12); c.drawString(20*mm,y,t); y-=6*mm; c.setFont('Helvetica',9)
    def tbl(df, cols):
        nonlocal y; colw = (W-40*mm)/len(cols); hy=y
        for i,col in enumerate(cols): c.setFont('Helvetica-Bold',9); c.drawString(20*mm+i*colw, hy, str(col))
        y-=5*mm; c.setFont('Helvetica',9)
        for _,row in df.head(10).iterrows():
            if y<25*mm: c.showPage(); y=H-20*mm
            for i,col in enumerate(cols): c.drawString(20*mm+i*colw, y, str(row[col])); 
            y-=5*mm
        y-=3*mm
    section('Positions & PnL'); p2=p.copy(); p2['PnL']=((p2['Last']-p2['Avg Cost'])*p2['Qty']).round(2); 
    if 'PnL %' not in p2.columns: p2['PnL %']=((p2['Last']/p2['Avg Cost']-1)*100).round(2)
    tbl(p2, ['Ticker','Qty','Avg Cost','Last','PnL','PnL %'])
    section('Signals'); tbl(s, [c for c in ['Ticker','Setup','Reason'] if c in s.columns])
    section('Breadth'); tbl(b, ['Metric','Value','Status'])
    section('Relative Strength'); tbl(r, ['Bucket','RS Trend'])
    c.showPage(); c.save(); buf.seek(0); return buf.read()

c1, c2, c3 = st.columns([1,1,2]); ts=_now()
with c1:
    if st.button('📦 Export CSV Pack', use_container_width=True):
        data=build_zip(pos,sig,br,rs); st.download_button('Download CSV ZIP', data=data, file_name=f'digest_{ts}.zip', mime='application/zip', use_container_width=True)
        _ensure('snapshots'); open(f'snapshots/digest_{ts}.zip','wb').write(data); st.success('Saved snapshots/digest_'+ts+'.zip')
with c2:
    if REPORTLAB_AVAILABLE and st.button('🧾 Export 1‑Pager PDF', use_container_width=True):
        pdf=build_pdf(pos,sig,br,rs); st.download_button('Download PDF', data=pdf, file_name=f'digest_{ts}.pdf', mime='application/pdf', use_container_width=True)
        _ensure('snapshots'); open(f'snapshots/digest_{ts}.pdf','wb').write(pdf); st.success('Saved snapshots/digest_'+ts+'.pdf')
