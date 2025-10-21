import os, json
from pathlib import Path
from datetime import datetime

DIGEST_OUT = Path(__file__).resolve().parents[3] / "digest_out"
DIGEST_OUT.mkdir(parents=True, exist_ok=True)

def build_digest_payload(setups: list[dict]) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {"generated_at": now, "count": len(setups), "items": setups}

def save_digest_preview(payload: dict) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fp = DIGEST_OUT / f"digest_{ts}.json"
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(fp)

# NOTE: Real SendGrid send can be added later; today we only build & save preview.
