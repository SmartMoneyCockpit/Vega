
# scripts/cleanup_pages.py
import os, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"

# Keep exactly these IB pages
KEEP = {
    "095_IB_Feed_Status.py",
    "096_IBKR_Ticker_ib.py",
}

# Candidates to delete (duplicates/collisions)
DELETE = [
    "091_IBKR_Live_Ticker.py",
    "91_IBKR_Live_Ticker.py",
    "090_IB_Feed_Status.py",
    "900_IB_Feed_Status.py",
]

def main():
    if not PAGES.exists():
        print(f"[cleanup] pages/ not found at {PAGES}")
        sys.exit(0)

    removed = []
    for name in DELETE:
        path = PAGES / name
        if path.exists():
            path.unlink()
            removed.append(name)

    # Warn if anything else collides
    names = {p.name for p in PAGES.glob("*.py")}
    live_dups = [n for n in names if "IBKR" in n and "Live" in n and "Ticker" in n and n not in KEEP and n not in DELETE]
    feed_dups = [n for n in names if "IB_Feed_Status" in n and n not in KEEP and n not in DELETE]

    print("[cleanup] removed:", removed or "none")
    print("[cleanup] remaining pages:", sorted(names))
    if live_dups:
        print("[cleanup] WARNING: Additional ticker-like pages still present:", live_dups)
    if feed_dups:
        print("[cleanup] WARNING: Additional feed-status-like pages still present:", feed_dups)

if __name__ == "__main__":
    main()
