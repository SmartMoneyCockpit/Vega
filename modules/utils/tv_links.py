def tv_symbol_url(s):
    s=(s or '').upper().replace('.TO','-TO')
    if s.startswith('^'):
        m={'^GSPC':'SPY','^NDX':'QQQ','^DJI':'DIA','^RUT':'IWM','^GSPTSE':'XIC-TO','^MXX':'EWW','^FTSE':'EWU','^GDAXI':'EWG','^FCHI':'EWQ','^STOXX50E':'FEZ','^N225':'EWJ','^HSI':'2800'}
        s=m.get(s,s[1:])
    if s.endswith('=X'): return f'https://www.tradingview.com/symbols/{s.replace("=X","")}/'
    if '=F' in s: return f'https://www.tradingview.com/symbols/{s.replace("=F","1!")}/'
    return f'https://www.tradingview.com/symbols/{s}/'
