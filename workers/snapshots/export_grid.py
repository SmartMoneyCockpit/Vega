from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

out_dir = Path("snapshots"); out_dir.mkdir(parents=True, exist_ok=True)
sectors = ["Technology","Financials","Healthcare","Energy","Consumer","Industrials","Utilities","Materials","Real Estate","Communication"]
df = pd.DataFrame({"Sector": sectors, "Change%":[0]*len(sectors)})
ts = datetime.now().strftime("%Y-%m-%d_%H%M"); png_path = out_dir / f"grid_snapshot_{ts}.png"; pdf_path = out_dir / f"grid_snapshot_{ts}.pdf"

fig, ax = plt.subplots(figsize=(10, 6)); ax.axis('off')
tbl = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1,1.4)
ax.set_title(f"Vega Grid Snapshot — {ts}", pad=12)
plt.savefig(png_path, bbox_inches='tight', dpi=150); plt.close(fig)

with PdfPages(pdf_path) as pdf:
    fig2, ax2 = plt.subplots(figsize=(10, 6)); ax2.axis('off')
    tbl2 = ax2.table(cellText=df.values, colLabels=df.columns, loc='center')
    tbl2.auto_set_font_size(False); tbl2.set_fontsize(10); tbl2.scale(1,1.4)
    ax2.set_title(f"Vega Grid Snapshot — {ts}", pad=12)
    pdf.savefig(fig2, bbox_inches='tight'); plt.close(fig2)

print("[snapshots] Wrote:", png_path, "and", pdf_path)
