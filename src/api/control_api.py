# app.py
from flask import Flask, request, jsonify, Response
import os
import pandas as pd
from modules.scanner.patterns import rising_wedge, falling_wedge, bearish_setup_score
from data.regions import REGIONS
from data.eodhd_adapter import get_eod_prices_csv

CHATGPT_CONTROL_TOKEN = os.getenv("CHATGPT_CONTROL_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "8080"))

app = Flask(__name__)

def _auth(req) -> bool:
    # Block if token not set OR header doesn't match
    token = req.headers.get("X-Control-Token", "")
    return bool(CHATGPT_CONTROL_TOKEN) and token == CHATGPT_CONTROL_TOKEN

@app.get("/health")
def health():
    return {"ok": True, "port": PORT}

def _df_json(df: pd.DataFrame) -> Response:
    return Response(df.to_json(orient="records"), mimetype="application/json")

@app.get("/report/rising_wedge")
def report_rising():
    if not _auth(request):
        return jsonify({"error": "unauthorized"}), 401
    region = request.args.get("region", "USA")
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
    return _df_json(out)

@app.get("/report/falling_wedge")
def report_falling():
    if not _auth(request):
        return jsonify({"error": "unauthorized"}), 401
    region = request.args.get("region", "USA")
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
    return _df_json(out)

@app.get("/report/downside_setups")
def report_downside():
    if not _auth(request):
        return jsonify({"error": "unauthorized"}), 401
    region = request.args.get("region", "USA")
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
    return _df_json(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
