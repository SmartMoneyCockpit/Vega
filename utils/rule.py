# utils/rules.py
import yaml
from pathlib import Path
from utils.data import get_price, get_vix

RULES_FILE = Path("config/alert_rules.yaml")

def load_rules():
    return yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))

def check_rearm_condition(r: dict) -> bool:
    # Basic implementations for examples provided
    if r["type"] == "price_cross":
        px = get_price(r["ticker"])
        band = r.get("rearm", {}).get("band_below")
        if r["direction"] == "above" and band is not None:
            return px < float(band)
        if r["direction"] == "below" and band is not None:
            return px > float(band)
    if r["type"] == "regime":
        vix = get_vix()
        rr = r.get("rearm", {})
        if rr.get("direction") == "below":
            return vix < float(rr.get("level", 0))
        if rr.get("direction") == "above":
            return vix > float(rr.get("level", 99))
    # conservative default: don't rearm
    return False
