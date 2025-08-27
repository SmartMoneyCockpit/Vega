# add_prefs_import.py
from pathlib import Path

IMPORT_LINE = "from utils.prefs_bootstrap import prefs\n"
root = Path(__file__).resolve().parent

def prepend_if_missing(path: Path):
    text = path.read_text(encoding="utf-8")
    if IMPORT_LINE.strip() in text:
        print(f"[skip] {path} (already has import)")
        return
    path.write_text(IMPORT_LINE + text, encoding="utf-8")
    print(f"[ok]   inserted import -> {path}")

# 1) Patch app.py if present anywhere under the project
apps = list(root.rglob("app.py"))
if apps:
    prepend_if_missing(apps[0])
else:
    print("[info] no app.py found (skipping)")

# 2) Patch every .py under any 'pages' directory
pages_dirs = [p for p in root.rglob("*") if p.is_dir() and p.name == "pages"]
if not pages_dirs:
    print("[info] no pages/ directories found")
else:
    for d in pages_dirs:
        for py in d.rglob("*.py"):
            prepend_if_missing(py)
