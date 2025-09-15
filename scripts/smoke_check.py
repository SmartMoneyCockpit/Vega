# Lightweight import test to fail fast on syntax/errors before Render deploy
import importlib
import sys

candidates = ["app", "main"]
ok = False
for name in candidates:
    try:
        importlib.import_module(name)
        print(f"[OK] Imported {name}.py")
        ok = True
        break
    except ModuleNotFoundError:
        continue

if not ok:
    print("[WARN] Could not import app.py or main.py — this is OK if your entrypoint has a different name.")
    sys.exit(0)
