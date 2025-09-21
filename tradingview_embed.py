# tradingview_embed.py
import urllib.parse as _uq
import streamlit as st

def _iframe(url: str, height: int = 720) -> None:
    st.markdown(
        f"""
        <div style="width:100%;height:{height}px;position:relative;">
          <iframe
            src="{url}"
            style="width:100%;height:100%;border:0;"
            frameborder="0"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            sandbox="allow-scripts allow-same-origin allow-popups"
          ></iframe>
        </div>
        """,
        unsafe_allow_html=True,
    )

def embed_tradingview(
    symbol: str = "NASDAQ:QQQ",
    height: int = 720,
    authenticated: bool = True,
    interval: str = "D",
    theme: str = "dark",
) -> None:
    """
    If authenticated=True -> use tradingview.com/chart which mirrors the user's *logged-in* account
    (more indicators, saved layouts). The browser will automatically send your TV cookies.

    If authenticated=False -> use the public widget (2 indicator limit).
    """
    symbol_q = _uq.quote(symbol)

    if authenticated:
        # Authenticated account view (uses your logged-in TradingView cookies in the browser).
        # If third-party cookies are blocked, the page will behave like logged out.
        url = (
            f"https://www.tradingview.com/chart/?symbol={symbol_q}"
            f"&utm_source=vega&feature=embed"
        )
        _iframe(url, height)
    else:
        # Public widget fallback (no login; 2 indicators max).
        # You can change interval/theme below if you like.
        params = {
            "symbol": symbol,
            "interval": interval,
            "theme": theme,
            "style": "1",
            "timezone": "Etc/UTC",
            "withdateranges": "1",
            "hide_side_toolbar": "0",
            "allow_symbol_change": "1",
            "save_image": "0",
            "locale": "en",
        }
        qs = _uq.urlencode(params, safe=":,")
        url = f"https://s.tradingview.com/widgetembed/?{qs}"
        _iframe(url, height)
