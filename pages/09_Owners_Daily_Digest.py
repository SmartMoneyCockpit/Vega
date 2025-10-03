
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
if not login_gate():
    pass

@st.cache_data(show_spinner=False)
def _now_str():
    return datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')

@st.cache_data(show_spinner=False)
def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path

def get_positions_df():
    if 'positions_df' in st.session_state and not st.session_state['positions_df'].empty:
        return st.session_state['positions_df']
    data = {'Ticker': ['HPR.TO', 'ZPR.TO', 'HSAV.TO'],
            'Qty': [1000, 1000, 200],
            'Avg Cost': [25.00, 9.50, 29.00],
            'Last': [25.40, 9.55, 29.02]}
    df = pd.DataFrame(data)
    df['PnL'] = (df['Last'] - df['Avg Cost']) * df['Qty']
    df['PnL %'] = np.where(df['Avg Cost']>0, (df['Last']/df['Avg Cost']-1)*100, 0.0)
    return df

def get_watchlist_signals_df():
    if 'signals_df' in st.session_state and not st.session_state['signals_df'].empty:
        return st.session_state['signals_df']
    return pd.DataFrame({
        'Ticker': ['SPY', 'SPXU', 'SQQQ', 'RWM', 'SLV', 'CPER'],
        'Country': ['USA','USA','USA','USA','USA','USA'],
        'Setup': ['Wait','Buy Today','Buy Today','Wait','Watch','Watch'],
        'Reason': ['Breadth weak','RS flip + options overpriced','NDX RS down','Risk-off fading','Trendline test','Copper trendline test']
    })

def get_breadth_df():
    if 'breadth_df' in st.session_state and not st.session_state['breadth_df'].empty:
        return st.session_state['breadth_df']
    return pd.DataFrame({
        'Metric': ['VIX','ADV/DEC (NYSE)','%>50DMA (SPX)','%>200DMA (SPX)'],
        'Value': [18.7, '0.82', '47%', '62%'],
        'Status': ['Neutral','Risk-Off','Caution','Healthy']
    })

def get_rs_df():
    if 'rs_df' in st.session_state and not st.session_state['rs_df'].empty:
        return st.session_state['rs_df']
    return pd.DataFrame({
        'Bucket': ['USA','Canada','Mexico','LATAM ex-MX','Tech','Industrials','Materials','Financials','Staples'],
        'RS Trend': ['🟡','🟡','🟢','🟡','🟠','🟢','🟡','🟡','🟢']
    })

def build_csv_zip(position_df, signals_df, breadth_df, rs_df) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('positions.csv', position_df.to_csv(index=False))
        zf.writestr('signals.csv', signals_df.to_csv(index=False))
        zf.writestr('breadth.csv', breadth_df.to_csv(index=False))
        zf.writestr('relative_strength.csv', rs_df.to_csv(index=False))
    buffer.seek(0)
    return buffer.read()

def build_pdf(position_df, signals_df, breadth_df, rs_df) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError('reportlab is not available in this environment')
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(20*mm, height-20*mm, 'Owner\\'s Daily Digest')
    c.setFont('Helvetica', 9)
    c.drawString(20*mm, height-26*mm, f'Generated: {ts}')
    y = height - 36*mm

    def section(title):
        nonlocal y
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(colors.darkblue)
        c.drawString(20*mm, y, title)
        y -= 6*mm
        c.setFillColor(colors.black)
        c.setFont('Helvetica', 9)

    def draw_table(df: pd.DataFrame, max_rows=8):
        nonlocal y
        cols = list(df.columns)
        col_width = (width - 40*mm) / len(cols)
        header_y = y
        for i, col in enumerate(cols):
            c.setFont('Helvetica-Bold', 9)
            c.drawString(20*mm + i*col_width, header_y, str(col))
        y -= 5*mm
        c.setFont('Helvetica', 9)
        for _, row in df.head(max_rows).iterrows():
            if y < 25*mm:
                c.showPage(); y = height - 20*mm
            for i, col in enumerate(cols):
                c.drawString(20*mm + i*col_width, y, str(row[col]))
            y -= 5*mm
        y -= 3*mm

    section('Positions & PnL')
    positions = position_df.copy()
    positions['PnL'] = positions['PnL'].round(2)
    positions['PnL %'] = positions['PnL %'].round(2)
    draw_table(positions[['Ticker','Qty','Avg Cost','Last','PnL','PnL %']])

    section('Signals (Trade Now vs Wait)')
    draw_table(signals_df[['Ticker','Setup','Reason']])

    section('Market Breadth / Internals')
    draw_table(breadth_df[['Metric','Value','Status']])

    section('Relative Strength (Country & Sectors)')
    draw_table(rs_df[['Bucket','RS Trend']])

    c.showPage(); c.save()
    buf.seek(0)
    return buf.read()

st.set_page_config(page_title='Owner\\'s Daily Digest', layout='wide')
st.title("Owner's Daily Digest – 1‑Pager & CSV Pack")

pos_df = get_positions_df()
sig_df = get_watchlist_signals_df()
br_df = get_breadth_df()
rs_df = get_rs_df()

left, right = st.columns([3,2])
with left:
    st.markdown('**Positions**')
    st.dataframe(pos_df, use_container_width=True)
    st.markdown('**Signals**')
    st.dataframe(sig_df, use_container_width=True)
with right:
    st.markdown('**Breadth**')
    st.dataframe(br_df, use_container_width=True)
    st.markdown('**Relative Strength**')
    st.dataframe(rs_df, use_container_width=True)

st.divider()
col1, col2 = st.columns([1,1])
ts = _now_str()

with col1:
    if st.button('📦 Export CSV Pack', use_container_width=True):
        zip_bytes = build_csv_zip(pos_df, sig_df, br_df, rs_df)
        st.download_button('Download CSV ZIP', data=zip_bytes, file_name=f'digest_{ts}.zip', mime='application/zip', use_container_width=True)
        outdir = _ensure_dir('snapshots')
        with open(os.path.join(outdir, f'digest_{ts}.zip'), 'wb') as f:
            f.write(zip_bytes)
        st.success(f'Saved to {outdir}/digest_{ts}.zip')

with col2:
    if REPORTLAB_AVAILABLE and st.button('🧾 Export 1‑Pager PDF', use_container_width=True):
        pdf = build_pdf(pos_df, sig_df, br_df, rs_df)
        st.download_button('Download PDF', data=pdf, file_name=f'digest_{ts}.pdf', mime='application/pdf', use_container_width=True)
        outdir = _ensure_dir('snapshots')
        with open(os.path.join(outdir, f'digest_{ts}.pdf'), 'wb') as f:
            f.write(pdf)
        st.success(f'Saved to {outdir}/digest_{ts}.pdf')
    elif not REPORTLAB_AVAILABLE:
        st.info('PDF export requires the **reportlab** package.')
