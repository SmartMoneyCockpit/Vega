import streamlit as st
import pandas as pd
import numpy as np
import io, zipfile, os
from datetime import datetime, timezone

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

from app_auth import login_gate
if not login_gate(): pass
from data_bridge import get_positions_df, get_signals_df, get_breadth_df, get_rs_df

@st.cache_data(show_spinner=False)
def _now_str():
    return datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')

@st.cache_data(show_spinner=False)
def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True); return path

def build_csv_zip(position_df, signals_df, breadth_df, rs_df) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('positions.csv', position_df.to_csv(index=False))
        zf.writestr('signals.csv', signals_df.to_csv(index=False))
        zf.writestr('breadth.csv', breadth_df.to_csv(index=False))
        zf.writestr('relative_strength.csv', rs_df.to_csv(index=False))
    buffer.seek(0); return buffer.read()

def build_pdf(position_df, signals_df, breadth_df, rs_df) -> bytes:
    if not REPORTLAB_AVAILABLE: raise RuntimeError('reportlab is not available')
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); width, height = A4
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold', 16); c.drawString(20*mm, height-20*mm, 'Owner\'s Daily Digest')
    c.setFont('Helvetica', 9); c.drawString(20*mm, height-26*mm, f'Generated: {ts}'); y = height - 36*mm
    def section(title):
        nonlocal y; c.setFont('Helvetica-Bold', 12); c.setFillColor(colors.darkblue); c.drawString(20*mm, y, title); y -= 6*mm; c.setFillColor(colors.black); c.setFont('Helvetica', 9)
    def draw_table(df: pd.DataFrame, max_rows=8):
        nonlocal y; cols = list(df.columns); col_width = (width - 40*mm) / len(cols); header_y = y
        for i, col in enumerate(cols): c.setFont('Helvetica-Bold', 9); c.drawString(20*mm + i*col_width, header_y, str(col))
        y -= 5*mm; c.setFont('Helvetica', 9)
        for _, row in df.head(max_rows).iterrows():
            if y < 25*mm: c.showPage(); y = height - 20*mm
            for i, col in enumerate(cols): c.drawString(20*mm + i*col_width, y, str(row[col]))
            y -= 5*mm
        y -= 3*mm
    section('Positions & PnL')
    positions = get_positions_df().copy()
    positions['PnL'] = ((positions['Last'] - positions['Avg Cost']) * positions['Qty']).round(2)
    if 'PnL %' not in positions.columns: positions['PnL %'] = (positions['Last']/positions['Avg Cost']-1).round(4) * 100
    positions['PnL %'] = positions['PnL %'].round(2)
    draw_table(positions[['Ticker','Qty','Avg Cost','Last','PnL','PnL %']])
    section('Signals (Trade Now vs Wait)')
    sig_df = get_signals_df(); cols = [c for c in ['Ticker','Setup','Reason'] if c in sig_df.columns]; draw_table(sig_df[cols])
    section('Market Breadth / Internals')
    draw_table(get_breadth_df()[['Metric','Value','Status']])
    section('Relative Strength (Country & Sectors)')
    draw_table(get_rs_df()[['Bucket','RS Trend']])
    c.showPage(); c.save(); buf.seek(0); return buf.read()

st.set_page_config(page_title='Owner\'s Daily Digest', layout='wide')
st.title("Owner's Daily Digest – 1-Pager & CSV Pack")
pos_df = get_positions_df(); sig_df = get_signals_df(); br_df = get_breadth_df(); rs_df = get_rs_df()
left, right = st.columns([3,2])
with left:
    st.markdown('**Positions**'); st.dataframe(pos_df, use_container_width=True)
    st.markdown('**Signals**'); st.dataframe(sig_df, use_container_width=True)
with right:
    st.markdown('**Breadth**'); st.dataframe(br_df, use_container_width=True)
    st.markdown('**Relative Strength**'); st.dataframe(rs_df, use_container_width=True)
st.divider(); col1, col2 = st.columns([1,1]); ts = _now_str()
with col1:
    if st.button('📦 Export CSV Pack', use_container_width=True):
        import io, zipfile
        zip_bytes = build_csv_zip(pos_df, sig_df, br_df, rs_df)
        st.download_button('Download CSV ZIP', data=zip_bytes, file_name=f'digest_{ts}.zip', mime='application/zip', use_container_width=True)
        outdir = _ensure_dir('snapshots'); open(os.path.join(outdir, f'digest_{ts}.zip'),'wb').write(zip_bytes); st.success(f'Saved to {outdir}/digest_{ts}.zip')
with col2:
    if REPORTLAB_AVAILABLE and st.button('🧾 Export 1-Pager PDF', use_container_width=True):
        pdf = build_pdf(pos_df, sig_df, br_df, rs_df)
        st.download_button('Download PDF', data=pdf, file_name=f'digest_{ts}.pdf', mime='application/pdf', use_container_width=True)
        outdir = _ensure_dir('snapshots'); open(os.path.join(outdir, f'digest_{ts}.pdf'),'wb').write(pdf); st.success(f'Saved to {outdir}/digest_{ts}.pdf')
    elif not REPORTLAB_AVAILABLE:
        st.info('PDF export requires the **reportlab** package.')
