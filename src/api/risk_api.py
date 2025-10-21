from flask import Flask, request, jsonify
from modules.risk.risk_scoring import full_report
from data.eodhd_adapter import get_eod_prices_csv

app = Flask(__name__)

@app.get("/risk/score")
def risk_score():
    symbol = request.args.get("symbol", "SPY")
    benchmark = request.args.get("benchmark", "SPY")
    period = request.args.get("period", "1y")

    df = get_eod_prices_csv(symbol, period=period)
    col = "adjusted_close" if "adjusted_close" in df.columns else "close"
    prices = df.set_index("date")[col]

    bench_prices = None
    if benchmark:
        bf = get_eod_prices_csv(benchmark, period=period)
        bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
        bench_prices = bf.set_index("date")[bcol]

    return jsonify(full_report(prices, bench_prices))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
