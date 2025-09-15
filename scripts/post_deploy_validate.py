#!/usr/bin/env python3
import sys, os, json, importlib

print("Post-deploy validation start")

# Basic imports
for mod in ["pandas","yfinance","yaml","ib_insync","streamlit"]:
    try:
        importlib.import_module(mod)
        print(f"[OK] import {mod}")
    except Exception as e:
        print(f"[WARN] import {mod} failed: {e}")

# Env presence
need = ["IB_HOST","IB_PORT","IB_CLIENT_ID","GOOGLE_SHEET_WATCHLIST_ID"]
report = {k: bool(os.getenv(k)) for k in need}
print("Env presence:", json.dumps(report))

print("Post-deploy validation complete")