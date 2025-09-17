from pathlib import Path
from datetime import datetime
import shutil

def main():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    src = Path("data/snapshots")
    if not src.exists(): return
    dst = Path(f"data/archive/{today}"); dst.mkdir(parents=True, exist_ok=True)
    for p in src.glob("*.csv"):
        shutil.copy2(p, dst / p.name)

if __name__ == "__main__":
    main()
