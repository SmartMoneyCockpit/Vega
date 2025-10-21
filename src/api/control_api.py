from flask import Flask, request, jsonify
import os, pandas as pd
from modules.scanner.patterns import rising_wedge, falling_wedge, bearish_setup_score
from data.regions import REGIONS
from data.eodhd_adapter import get_eod_prices_csv

CHATGPT_CONTROL_TOKEN = os.getenv("CHATGPT_CONTROL_TOKEN","").strip()
app = Flask(__name__)

def _auth(req):
    tok = req.headers.get("X-Control-Token","")
    return CHATGPT_CONTROL_TOKEN and tok == CHATGPT_CONTROL_TOKEN

@app.get("/report/rising_wedge")
def report_rising():
    if not _auth(request): return jsonify({"error":"unauthorized"}), 401
    region = request.args.get("region","USA")
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "Match": bool(rising_wedge(s,60))})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:120]})
    out = pd.DataFrame(rows)
    out = out[out["Match"]==True]
    return out.to_json(orient="records")

@app.get("/report/falling_wedge")
def report_falling():
    if not _auth(request): return jsonify({"error":"unauthorized"}), 401
    region = request.args.get("region","USA")
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "Match": bool(falling_wedge(s,60))})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:120]})
    out = pd.DataFrame(rows)
    out = out[out["Match"]==True]
    return out.to_json(orient="records")

@app.get("/report/downside_setups")
def report_downside():
    if not _auth(request): return jsonify({"error":"unauthorized"}), 401
    region = request.args.get("region","USA")
    syms = REGIONS.get(region, [])
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period="6m")
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            rows.append({"Symbol": sym, "BearishScore": bearish_setup_score(s,20)})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:120]})
    out = pd.DataFrame(rows).sort_values("BearishScore", ascending=False)
    return out.to_json(orient="records")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
