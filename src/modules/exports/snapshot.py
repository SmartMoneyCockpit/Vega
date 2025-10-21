from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

EXPORT_DIR = Path(__file__).resolve().parents[3] / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_df_csv(df: pd.DataFrame, name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = EXPORT_DIR / f"{name}_{ts}.csv"
    df.to_csv(p, index=False)
    return str(p)

def export_series_png(series: pd.Series, name: str, title: str | None = None) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = EXPORT_DIR / f"{name}_{ts}.png"
    fig = plt.figure()
    ax = plt.gca()
    series.plot(kind="bar", ax=ax)
    ax.set_title(title or name)
    fig.tight_layout()
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    return str(p)
