
from __future__ import annotations
import os, hashlib, datetime as dt

def file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    outdir = os.path.join("changes")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"file_inventory_{dt.date.today().isoformat()}.txt")
    removed = []
    with open(out, 'w', encoding='utf-8') as w:
        w.write("# File Inventory\n")
        for dp, _, fn in os.walk('.'):
            if dp.startswith("./.git"): 
                continue
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    c = file_checksum(p)
                    s = os.path.getsize(p)
                    w.write(f"{p}\t{s}\t{c}\n")
                except Exception:
                    pass
        if removed:
            w.write("\n# Removed Files\n")
            for r in removed:
                w.write(f"{r}\n")
    print(f"Inventory written: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
