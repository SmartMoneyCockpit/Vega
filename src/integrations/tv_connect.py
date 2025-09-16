# tv_connect.py — drop‑in module for Vega Cockpit (Streamlit)
# Purpose: Open the user's TradingView (TV) in their already‑logged‑in browser
# without any API keys or credentials, plus offer optional embedded previews.
#
# Usage:
# 1) Put this file somewhere importable (e.g., src/integrations/tv_connect.py)
# 2) From app.py: `from src.integrations.tv_connect import tradingview_panel`
# 3) Call `tradingview_panel("AAPL", exchange="NASDAQ")` or pass a list.
#
# Notes:
# - "Open in TradingView" buttons open a new tab using standard TV links.
# - If you’re logged into TV in your browser, you land in your account context.
# - Embeds use TradingView’s public widget (no login context). Great as a preview.

from __future__ import annotations
import json
from typing import List, Dict, Optional

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# -----------------------------
# Core URL helpers
# -----------------------------

TV_BASE_CHART = "https://www.tradingview.com/chart/"
TV_BASE_SYMBOL = "https://www.tradingview.com/symbols/"

# Common TV exchange prefixes (expand as needed)
_EX_PREFIX = {
    "NASDAQ": "NASDAQ:",
    "NYSE": "NYSE:",
    "AMEX": "AMEX:",
    "TSX": "TSX:",
    "TSXV": "TSXV:",
    "CSE": "CSE:",
    "BATS": "BATS:",
    "NYSEARCA": "AMEX:",  # TV often maps many ETFs under AMEX
    "NYSEMKT": "AMEX:",
    "BMV": "BMV:",  # Mexico
}

# Valid TV intervals for the widget (not exhaustive)
_VALID_INTERVALS = {"1", "3", "5", "15", "30", "60", "120", "180", "240", "D", "W", "M"}


def tv_symbol(exchange: str, ticker: str) -> str:
    """Return TradingView's SYMBOL string like 'NASDAQ:AAPL'."""
    ex = (exchange or "").upper()
    prefix = _EX_PREFIX.get(ex, f"{ex}:")
    return f"{prefix}{ticker.upper()}"


def tv_chart_url(symbol: str, interval: str = "D", layout: Optional[str] = None) -> str:
    """Build a /chart URL that opens an interactive chart. If logged in, it uses the user's context.
    Example: https://www.tradingview.com/chart/?symbol=NASDAQ:AAPL&interval=60
    """
    q = [f"symbol={symbol}", f"interval={interval}"]
    if layout:
        q.append(f"layout={layout}")  # use a saved layout id if you have one
    return f"{TV_BASE_CHART}?" + "&".join(q)


def tv_symbol_overview_url(symbol: str) -> str:
    """Build a /symbols/ overview URL. Example: https://www.tradingview.com/symbols/NASDAQ-AAPL/"""
    # TV uses hyphen between exchange and ticker in this endpoint
    ex, tick = symbol.split(":", 1)
    return f"{TV_BASE_SYMBOL}{ex}-{tick}/"


# -----------------------------
# Streamlit UI pieces
# -----------------------------

_WIDGET_TEMPLATE = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="{dom_id}"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": {height},
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "light",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "hide_top_toolbar": false,
    "withdateranges": true,
    "allow_symbol_change": true,
    "hide_legend": false,
    "save_image": false,
    "studies": {studies},
    "container_id": "{dom_id}"
  }});
</script>
<!-- TradingView Widget END -->
"""


def tv_embed(symbol: str, interval: str = "D", height: int = 560, studies: Optional[List[str]] = None):
    """Render an embedded TradingView widget as a preview (no login required).
    studies: list of study ids (e.g., ["MASimple@tv-basicstudies", "RSI@tv-basicstudies"]).
    """
    interval = interval if interval in _VALID_INTERVALS else "D"
    dom_id = f"tv_{symbol.replace(':', '_')}_{interval}"
    studies = studies or ["MASimple@tv-basicstudies", "RSI@tv-basicstudies"]
    html = _WIDGET_TEMPLATE.format(
        dom_id=dom_id,
        symbol=symbol,
        interval=interval,
        height=int(height),
        studies=json.dumps(studies),
    )
    components.html(html, height=height + 20)


# -----------------------------
# High-level panel
# -----------------------------

def tradingview_panel(
    items: List[Dict[str, str]] | pd.DataFrame | str,
    exchange: Optional[str] = None,
    *,
    default_interval: str = "D",
    show_embed_preview: bool = True,
    embed_height: int = 520,
) -> None:
    """Render a TradingView Connect panel.

    items: list/df of {"symbol": "AAPL", "exchange": "NASDAQ", "label": "Apple"}
           OR a single ticker string like "AAPL" with exchange set via param.
    exchange: fallback exchange for any items missing it.
    default_interval: TV interval for links and embeds (e.g., "D", "60", "240").
    show_embed_preview: if True, show one live preview under the selected row.
    embed_height: px height for the embedded preview.
    """
    st.subheader("TradingView Connect (no API)")

    # Normalize input -> DataFrame
    if isinstance(items, str):
        items = [{"symbol": items, "exchange": exchange or "NASDAQ", "label": items.upper()}]
    elif isinstance(items, pd.DataFrame):
        items = items.to_dict(orient="records")

    data = []
    for row in items:  # type: ignore
        sym = row.get("symbol") or row.get("ticker")
        ex = (row.get("exchange") or exchange or "NASDAQ").upper()
        label = row.get("label") or sym
        full = tv_symbol(ex, sym)
        data.append({
            "Label": label,
            "TV Symbol": full,
            "Chart": tv_chart_url(full, interval=default_interval),
            "Overview": tv_symbol_overview_url(full),
        })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Selection + actions
    st.markdown("**Open selected in your TradingView (new tab):**")
    idx = st.number_input("Row #", min_value=0, max_value=len(df) - 1, value=0, step=1, key="tv_row")
    row = df.iloc[int(idx)] if len(df) else None

    cols = st.columns(3)
    if row is not None:
        with cols[0]:
            st.link_button("Open Chart", row["Chart"])  # opens in new tab
        with cols[1]:
            st.link_button("Open Overview", row["Overview"])  # opens in new tab
        with cols[2]:
            new_interval = st.selectbox("Interval", sorted(_VALID_INTERVALS), index=sorted(_VALID_INTERVALS).index(default_interval) if default_interval in _VALID_INTERVALS else 9, key="tv_ivl")
            st.session_state["tv_interval"] = new_interval

        if show_embed_preview:
            st.divider()
            st.caption("Embedded preview (public widget)")
            tv_embed(row["TV Symbol"], interval=st.session_state.get("tv_interval", default_interval), height=embed_height)


# -----------------------------
# Demo (remove in production)
# -----------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="TV Connect Demo", layout="wide")
    demo = [
        {"label": "Apple", "symbol": "AAPL", "exchange": "NASDAQ"},
        {"label": "S&P 500 ETF", "symbol": "SPY", "exchange": "AMEX"},
        {"label": "NVIDIA", "symbol": "NVDA", "exchange": "NASDAQ"},
        {"label": "USD/MXN", "symbol": "USDMXN", "exchange": "FX"},  # will render as FX:USDMXN
    ]
    tradingview_panel(demo, default_interval="60")
