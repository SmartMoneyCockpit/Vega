
import json
from typing import Literal
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


def chart_spec(df: pd.DataFrame, theme: Literal["light","dark"]="dark", main_height:int=820):
    """Return charts spec with adjustable heights. Child panes scale from main pane."""
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

    macd_line = {"type":"Line","data":_to_lw(df.set_index("time")["macd"]), "options":{"lineWidth":1}}
    macd_sig  = {"type":"Line","data":_to_lw(df.set_index("time")["macd_sig"]), "options":{"lineWidth":1}}
    macd_hist = {"type":"Histogram","data":[{"time": int(pd.Timestamp(t).timestamp()), "value": float(v)} for t, v in df.set_index("time")["macd_hist"].dropna().items()]}
    rsi_line = {"type":"Line","data":_to_lw(df.set_index("time")["rsi"]), "options":{"lineWidth":1}}
    obv_line = {"type":"Line","data":_to_lw(df.set_index("time")["obv"]), "options":{"lineWidth":1}}
    atr_line = {"type":"Line","data":_to_lw(df.set_index("time")["atr"]), "options":{"lineWidth":1}}

    # Scale child panes based on main height
    macd_h = max(int(main_height*0.25), 140)
    small_h = max(int(main_height*0.18), 110)

    charts = [
        {
            "width": "100%",
            "height": int(main_height),
            "options": opts,
            "series": [candles, ema9, ema21, ema50, ema200, bb_mid, bb_up, bb_lo, ich_a, ich_b],
        },
        {"width": "100%","height": macd_h,"options": opts,"series": [macd_line, macd_sig, macd_hist]},
        {"width": "100%","height": small_h,"options": opts,"series": [rsi_line],"priceScale": {"mode": 1, "autoScale": True}},
        {"width": "100%","height": small_h,"options": opts,"series": [obv_line]},
        {"width": "100%","height": small_h,"options": opts,"series": [atr_line]},
    ]
    return charts


def render(df: pd.DataFrame, theme: Literal["light","dark"]="dark", main_height:int=820):
    spec = chart_spec(df, theme=theme, main_height=main_height)
    renderLightweightCharts(spec, key=f"vega-native-charts-{theme}-{main_height}")
