import datetime as dt
from pathlib import Path

def ensure_dir(p: str | Path) -> Path:
    p = Path(p); p.mkdir(parents=True, exist_ok=True); return p

def save_snapshot(fig_bytes: bytes, outdir: str, prefix: str="panel") -> str:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = ensure_dir(outdir)
    path = folder / f"{prefix}-{ts}.png"
    with open(path, "wb") as f:
        f.write(fig_bytes)
    return str(path)
