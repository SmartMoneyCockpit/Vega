def tv_symbol_url(symbol: str) -> str:
    """
    Build a TradingView symbol URL that opens in a new tab.
    Handles common cases (indices via ETF proxy; FX with =X; futures like CL=F -> CL1!).
    """
    if not symbol:
        return "https://www.tradingview.com/"
    s = symbol.upper().strip().replace(".TO","-TO")
    if s.startswith("^"):
        idx_map = {"^GSPC":"SPY","^NDX":"QQQ","^DJI":"DIA","^RUT":"IWM","^GSPTSE":"XIC-TO",
                   "^MXX":"EWW","^FTSE":"EWU","^GDAXI":"EWG","^FCHI":"EWQ","^STOXX50E":"FEZ",
                   "^N225":"EWJ","^HSI":"2800"}
        s = idx_map.get(s, s[1:])
        if s.startswith("^"):
            s = s[1:]
    if s.endswith("=X"):
        pair = s.replace("=X","")
        return f"https://www.tradingview.com/symbols/{pair}/"
    if "=F" in s:
        root = s.replace("=F","1!")
        return f"https://www.tradingview.com/symbols/{root}/"
    return f"https://www.tradingview.com/symbols/{s}/"
