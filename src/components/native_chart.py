
import json
from typing import Literal, Tuple
import pandas as pd

from streamlit_lightweight_charts import renderLightweightCharts


def _to_lw(series: pd.Series):
    return [{"time": int(pd.Timestamp(t).timestamp()), "value": float(v)} for t, v in series.dropna().items()]


def _candles_to_lw(df: pd.DataFrame, use_heikin: bool = True):
    cols = ("ha_open","ha_high","ha_low","ha_close") if use_heikin else ("open","high","low","close")
    out = []
    for t, row in df.dropna(subset=list(cols)).iterrows():
        out.append({
            "time": int(pd.Timestamp(t).timestamp()),
            "open": float(row[cols[0]]),
            "high": float(row[cols[1]]),
            "low":  float(row[cols[2]]),
            "close":float(row[cols[3]]),
        })
    return out


def chart_spec(df: pd.DataFrame, theme: Literal["light","dark"]="dark"):
    """Return a list of chart specs suitable for renderLightweightCharts (multi-pane)."""
    opts = {
        "layout": {"background": {"type": "solid", "color": "#FFFFFF" if theme=="light" else "#0e1117"},
                   "textColor": "#222" if theme=="light" else "#DDD"},
        "timeScale": {"timeVisible": True, "secondsVisible": False, "borderVisible": False},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"visible": False}},
        "crosshair": {"mode": 1},
        "rightPriceScale": {"borderVisible": False},
        "watermark": {"visible": False},
    }

    candles = {
        "type": "Candlestick",
        "data": _candles_to_lw(df.set_index("time"), use_heikin=True),
        "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False, "wickUpColor": "#26a69a", "wickDownColor": "#ef5350"},
    }

    ema9  = {"type": "Line", "data": _to_lw(df.set_index("time")["ema9"]),  "options": {"lineWidth": 1}}
    ema21 = {"type": "Line", "data": _to_lw(df.set_index("time")["ema21"]), "options": {"lineWidth": 1}}
    ema50 = {"type": "Line", "data": _to_lw(df.set_index("time")["ema50"]), "options": {"lineWidth": 1}}
    ema200= {"type": "Line", "data": _to_lw(df.set_index("time")["ema200"]), "options": {"lineWidth": 1}}

    bb_mid = {"type":"Line","data":_to_lw(df.set_index("time")["bb_mid"]), "options":{"lineWidth":1}}
    bb_up  = {"type":"Line","data":_to_lw(df.set_index("time")["bb_up"]),  "options":{"lineWidth":1}}
    bb_lo  = {"type":"Line","data":_to_lw(df.set_index("time")["bb_lo"]),  "options":{"lineWidth":1}}

    ich_a  = {"type":"Area","data":_to_lw(df.set_index("time")["ichimoku_a"])}
    ich_b  = {"type":"Area","data":_to_lw(df.set_index("time")["ichimoku_b"])}

    # Pane 2: MACD
    macd_line = {"type":"Line","data":_to_lw(df.set_index("time")["macd"]), "options":{"lineWidth":1}}
    macd_sig  = {"type":"Line","data":_to_lw(df.set_index("time")["macd_sig"]), "options":{"lineWidth":1}}
    macd_hist = {"type":"Histogram","data":[{"time": int(pd.Timestamp(t).timestamp()), "value": float(v)} for t, v in df.set_index("time")["macd_hist"].dropna().items()]}

    # Pane 3: RSI
    rsi_line = {"type":"Line","data":_to_lw(df.set_index("time")["rsi"]), "options":{"lineWidth":1}}

    # Pane 4: OBV
    obv_line = {"type":"Line","data":_to_lw(df.set_index("time")["obv"]), "options":{"lineWidth":1}}

    # Pane 5: ATR
    atr_line = {"type":"Line","data":_to_lw(df.set_index("time")["atr"]), "options":{"lineWidth":1}}

    charts = [
        {
            "width": "100%",
            "height": 400,
            "options": opts,
            "series": [candles, ema9, ema21, ema50, ema200, bb_mid, bb_up, bb_lo, ich_a, ich_b],
        },
        {
            "width": "100%",
            "height": 160,
            "options": opts,
            "series": [macd_line, macd_sig, macd_hist],
        },
        {
            "width": "100%",
            "height": 120,
            "options": opts,
            "series": [rsi_line],
            "priceScale": {"mode": 1, "autoScale": True},
        },
        {
            "width": "100%",
            "height": 120,
            "options": opts,
            "series": [obv_line],
        },
        {
            "width": "100%",
            "height": 120,
            "options": opts,
            "series": [atr_line],
        },
    ]
    return charts


def render(df: pd.DataFrame, theme: Literal["light","dark"]="dark"):
    spec = chart_spec(df, theme=theme)
    renderLightweightCharts(spec, key="vega-native-charts")
