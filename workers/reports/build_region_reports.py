from pathlib import Path
from datetime import datetime
import pandas as pd

def build(region_key, title):
    snap = Path(f"data/snapshots/{region_key.lower()}_indices.csv")
    out = Path(f"reports/{region_key}"); out.mkdir(parents=True, exist_ok=True)
    if not snap.exists():
        out.joinpath("latest.md").write_text(f"# {title}\nNo data yet.\n"); return
    df = pd.read_csv(snap)
    buy = df[df["decision"].str.contains("🟢", na=False)][["symbol","price","chg_1d","rs"]]
    wait = df[df["decision"].str.contains("🟡", na=False)][["symbol","price","chg_1d","rs"]]
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    parts=[f"# {title} — {ts}",""]
    if not buy.empty: parts+=["## Buy Today", buy.to_markdown(index=False), ""]
    if not wait.empty: parts+=["## Buy Next Few Days", wait.to_markdown(index=False), ""]
    if len(parts)==2: parts.append("_No opportunities identified by rules right now._")
    out.joinpath("latest.md").write_text("\n".join(parts))

if __name__ == "__main__":
    build("NA","North America Report"); build("EU","Europe Report"); build("APAC","APAC Report")
    print("Reports written → reports/<REGION>/latest.md")
