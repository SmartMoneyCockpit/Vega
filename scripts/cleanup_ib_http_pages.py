# scripts/cleanup_ib_http_pages.py
import os, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"

DELETE = [
    "90_IBKR_Quick_Test.py",
    "92_IBKR_Order_Ticket.py",
]

def main():
    removed = []
    for name in DELETE:
        p = PAGES / name
        if p.exists():
            p.unlink()
            removed.append(name)
    print("[cleanup] removed:", removed or "none")
    print("[cleanup] done.")

if __name__ == "__main__":
    main()
