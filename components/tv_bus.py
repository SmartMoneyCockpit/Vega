
# src/components/tv_bus.py
import json
from streamlit.components.v1 import html

def push_symbol(symbol: str, interval: str | None = None):
    payload = {"type": "VEGA_SET_SYMBOL", "symbol": symbol}
    if interval:
        payload["interval"] = interval
    html(f"<script>try{{window.parent.postMessage({json.dumps(payload)}, '*');}}catch(e){{}}</script>", height=0)
