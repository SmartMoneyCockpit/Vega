# modules/utils/tv_links.py

"""
TradingView link builder.

Accepts:
- Plain tickers      → "SPY"
- Index aliases      → "^GSPC", "^NDX", etc. (mapped to liquid ETF proxies)
- FX pairs (Yahoo)   → "USDCAD=X"  → "USDCAD"
- Futures (Yahoo)    → "CL=F"      → "CL1!"
- Exchange suffixes  → ".TO"→"TSX:", ".V"→"TSXV:", ".CN"→"CSE:", ".HK"→"HKEX:", ".L"→"LSE:",
                       ".AX"→"ASX:", ".SS"→"SSE:"
If the input looks like a long **name** (e.g., "SPDR S&P 500 ETF"), we try a tiny
fallback map to a real ticker first.
"""

from typing import Optional

# Minimal "name → ticker" safety net for common ETFs
_NAME_TO_TICKER = {
    "SPDR S&P 500 ETF": "SPY",
    "INVESCO QQQ TRUST": "QQQ",
    "ISHARES RUSSELL 2000": "IWM",
    "BMO GROWTH ETF": "ZGRO.TO",
}


def _sanitize(s: str) -> str:
    return (s or "").strip().upper()


def _map_index_to_proxy(s: str) -> Optional[str]:
    if not s.startswith("^"):
        return None
    m = {
        "^GSPC": "SPY",
        "^NDX": "QQQ",
        "^DJI": "DIA",
        "^RUT": "IWM",
        "^GSPTSE": "XIC.TO",
        "^MXX": "EWW",
        "^FTSE": "EWU",
        "^GDAXI": "EWG",
        "^FCHI": "EWQ",
        "^STOXX50E": "FEZ",
        "^N225": "EWJ",
        "^HSI": "2800.HK",
    }
    return m.get(s)


def _map_suffix_to_prefix(s: str) -> Optional[str]:
    """
    Convert Yahoo-style suffix tickers into TradingView <EXCHANGE:SYMBOL>.
    Returns a 'EXCHANGE:SYMBOL' string or None if not applicable.
    """
    suffix_map = {
        ".TO": "TSX:",     # Toronto
        ".V": "TSXV:",     # TSX Venture
        ".CN": "CSE:",     # CSE Canada
        ".HK": "HKEX:",    # Hong Kong
        ".L": "LSE:",      # London
        ".AX": "ASX:",     # Australia
        ".SS": "SSE:",     # Shanghai
        ".SZ": "SZSE:",    # Shenzhen
        ".NE": "NEO:",     # NEO
    }
    for suf, pref in suffix_map.items():
        if s.endswith(suf):
            sym = s[: -len(suf)]
            if sym:  # guard against empty
                return f"{pref}{sym}"
    return None


def tv_symbol_url(symbol: str) -> str:
    """
    Return a TradingView symbol URL (always ends with '/').
    """
    if not symbol:
        return "https://www.tradingview.com/"

    s = _sanitize(symbol)

    # If it looks like a long name, try the tiny name→ticker map
    if " " in s and s in _NAME_TO_TICKER:
        s = _sanitize(_NAME_TO_TICKER[s])

    # Already fully qualified (e.g., 'OANDA:DE30EUR', 'TSX:XIC')
    if ":" in s and not s.endswith(":"):
        return f"https://www.tradingview.com/symbols/{s}/"

    # Yahoo FX → TV pair
    if s.endswith("=X"):
        pair = s.replace("=X", "")
        return f"https://www.tradingview.com/symbols/{pair}/"

    # Yahoo futures → front continuous
    if "=F" in s:
        root = s.replace("=F", "1!")
        return f"https://www.tradingview.com/symbols/{root}/"

    # Yahoo index aliases → ETF proxies (more reliable for public view)
    proxy = _map_index_to_proxy(s)
    if proxy:
        s = _sanitize(proxy)

    # Exchange suffixes (Yahoo) → TradingView prefixes
    pref = _map_suffix_to_prefix(s)
    if pref:
        return f"https://www.tradingview.com/symbols/{pref}/"

    # Fallback: plain ticker
    return f"https://www.tradingview.com/symbols/{s}/"
