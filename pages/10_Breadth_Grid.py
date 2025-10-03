import streamlit as st, os
from datetime import datetime
from app_auth import login_gate
if not login_gate(): pass
from data_bridge import get_breadth_df

st.set_page_config(page_title="Breadth / Grid", layout="wide")
st.title("Breadth / Grid Panel")
df = get_breadth_df()
st.dataframe(df, use_container_width=True)

if st.button("📸 Save PNG Snapshot"):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(); ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center'); table.scale(1, 2)
    os.makedirs('snapshots', exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S'); path = f'snapshots/breadth_{ts}.png'
    fig.savefig(path, bbox_inches='tight', dpi=200); st.success(f"Saved {path}")
