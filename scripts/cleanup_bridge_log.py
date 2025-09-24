# scripts/cleanup_bridge_log.py
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
TARGET = PAGES / "93_IBKR_Bridge_Log.py"
if TARGET.exists():
    TARGET.unlink()
    print("[cleanup] removed 93_IBKR_Bridge_Log.py")
else:
    print("[cleanup] nothing to remove")
