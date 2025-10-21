import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

EXPORT_DIR = Path(__file__).resolve().parents[3] / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_dataframe_png(df: pd.DataFrame, title: str = "Snapshot"):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    png_path = EXPORT_DIR / f"{title.replace(' ','_')}_{ts}.png"
    fig = plt.figure()
    try:
        df.plot(ax=plt.gca())
    except Exception:
        plt.text(0.1, 0.9, f"{title}", transform=plt.gca().transAxes)
        plt.axis('off')
    plt.title(title)
    fig.savefig(png_path, bbox_inches='tight')
    plt.close(fig)
    return str(png_path)

def export_dataframe_csv(df: pd.DataFrame, title: str = "Snapshot"):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = EXPORT_DIR / f"{title.replace(' ','_')}_{ts}.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)
