# src/api/control_api.py — Vega API (FastAPI for Render/uvicorn)
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os, sys
import pandas as pd
from pathlib import Path

# --- Make sure repo root is importable so "modules/..." works ---
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --- Domain logic imports ---
from modules.scanner.patterns import rising_wedge, falling_wedge, bearish_setup_score
from data.regions import REGIONS
from data.eodhd_adapter import get_eod_prices_csv

CHATGPT_CONTROL_TOKEN = os.getenv("CHATGPT_CONTROL_TOKEN", "").strip()

app = FastAPI(title="Vega API", version="1.0.0")

# --------------------------------------------------------------------
def _check_auth(request: Request):
    tok = request.headers.get("X-Control-Token", "")
    if not CHATGPT_CONTROL_TOKEN or tok != CHATGPT_CONTROL_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health():
    # Fast health for Render
    return {"ok": True}


@app.get("/report/rising_wedge")
def report_rising(request: Request, region: str = "USA"):
    _check_auth(request)
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "Match": bool(rising_wedge(s, 60))})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:200]})
    out = pd.DataFrame(rows)
    if "Match" in out.columns:
        out = out[out["Match"] == True]
    return JSONResponse(out.to_dict(orient="records"))


@app.get("/report/falling_wedge")
def report_falling(request: Request, region: str = "USA"):
    _check_auth(request)
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "Match": bool(falling_wedge(s, 60))})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:200]})
    out = pd.DataFrame(rows)
    if "Match" in out.columns:
        out = out[out["Match"] == True]
    return JSONResponse(out.to_dict(orient="records"))


@app.get("/report/downside_setups")
def report_downside(request: Request, region: str = "USA"):
    _check_auth(request)
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "BearishScore": float(bearish_setup_score(s, 20))})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:200]})
    out = pd.DataFrame(rows)
    if "BearishScore" in out.columns:
        out = out.sort_values("BearishScore", ascending=False)
    return JSONResponse(out.to_dict(orient="records"))
