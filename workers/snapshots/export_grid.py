from pathlib import Path
from datetime import datetime
out_dir = Path("snapshots")
out_dir.mkdir(parents=True, exist_ok=True)
ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
(out_dir / f"grid_snapshot_{ts}.txt").write_text("Snapshot placeholder — replace with real PNG/PDF export.")
print("Wrote", out_dir / f"grid_snapshot_{ts}.txt")
