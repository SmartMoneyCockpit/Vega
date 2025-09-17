from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def export_for(region_key: str):
    p = Path(f"data/snapshots/{region_key}_indices.csv")
    if not p.exists(): return
    df = pd.read_csv(p)
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = Path("reports/snapshots"); out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{region_key}_scorecard_{ts}.png"
    pdf = out_dir / f"{region_key}_scorecard_{ts}.pdf"

    cols = ["symbol","price","chg_1d","rs","decision"]
    view = df[cols] if set(cols).issubset(df.columns) else df

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis('off')
    tbl = ax.table(cellText=view.values, colLabels=view.columns, loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1,1.3)
    ax.set_title(f"{region_key.upper()} — Index Scorecard — {ts}", pad=12)
    plt.savefig(png, bbox_inches='tight', dpi=150); plt.close(fig)

    with PdfPages(pdf) as pdfp:
        fig2, ax2 = plt.subplots(figsize=(11, 6))
        ax2.axis('off')
        tbl2 = ax2.table(cellText=view.values, colLabels=view.columns, loc='center')
        tbl2.auto_set_font_size(False); tbl2.set_fontsize(9); tbl2.scale(1,1.3)
        ax2.set_title(f"{region_key.upper()} — Index Scorecard — {ts}", pad=12)
        pdfp.savefig(fig2, bbox_inches='tight'); plt.close(fig2)

def main():
    for rk in ["na","eu","apac"]:
        export_for(rk)

if __name__ == "__main__":
    main()
