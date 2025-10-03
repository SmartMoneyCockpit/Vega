
import streamlit as st, pandas as pd, os
from datetime import datetime
from app_auth import login_gate
if not login_gate():
    pass

st.set_page_config(page_title="Breadth / Grid", layout="wide")
st.title("Breadth / Grid Panel")

def get_breadth():
    if 'breadth_df' in st.session_state and not st.session_state['breadth_df'].empty:
        return st.session_state['breadth_df']
    return pd.DataFrame({
        'Metric': ['VIX','ADV/DEC (NYSE)','%>50DMA (SPX)','%>200DMA (SPX)'],
        'Value': [18.7, '0.82', '47%', '62%'],
        'Status': ['Neutral','Risk-Off','Caution','Healthy']
    })

df = get_breadth()
st.dataframe(df, use_container_width=True)

if st.button("📸 Save PNG Snapshot"):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    table.scale(1, 2)
    os.makedirs('snapshots', exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    path = f'snapshots/breadth_{ts}.png'
    fig.savefig(path, bbox_inches='tight', dpi=200)
    st.success(f"Saved {path}")
