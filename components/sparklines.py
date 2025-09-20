
# components/sparklines.py
from __future__ import annotations
import os, pandas as pd, matplotlib.pyplot as plt
from typing import Optional

# Note: keep charts neutral (no fixed colors/styles as general rule).
def save_sparkline(symbol: str, metric: str, df: pd.DataFrame, outdir: str = "vault/cache/sparklines", width: int = 160, height: int = 40) -> Optional[str]:
    """Saves a tiny PNG sparkline for a given metric timeseries.
    df must have columns: date, value (already filtered to target metric).
    Returns path to PNG or None.
    """
    os.makedirs(os.path.join(outdir, metric), exist_ok=True)
    path = os.path.join(outdir, metric, f"{symbol.upper()}.png")
    try:
        fig = plt.figure(figsize=(width/96, height/96), dpi=96)
        ax = fig.add_subplot(111)
        ax.plot(df["date"], df["value"])
        ax.axis('off')
        fig.tight_layout(pad=0)
        fig.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return path
    except Exception:
        return None
