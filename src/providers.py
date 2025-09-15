from __future__ import annotations
from typing import Optional
import pandas as pd

try:
    from polygon import RESTClient as PolygonClient  # type: ignore
except Exception:
    PolygonClient = None  # type: ignore

try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None  # type: ignore

class MarketDataProvider:
    def __init__(self, prefer: list[str]):
        self.order = prefer

    def fetch_ohlc(self, symbol: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        for name in self.order:
            func = getattr(self, f"_fetch_{name}", None)
            if callable(func):
                try:
                    df = func(symbol, period, interval)
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        return df
                except Exception:
                    continue
        return None

    def _fetch_ibkr(self, symbol: str, period: str, interval: str):
        return None  # placeholder

    def _fetch_tradingview(self, symbol: str, period: str, interval: str):
        return None  # placeholder

    def _fetch_polygon(self, symbol: str, period: str, interval: str):
        if PolygonClient is None:
            return None
        return None  # placeholder

    def _fetch_public(self, symbol: str, period: str, interval: str):
        if yf is None:
            return None
        t = yf.Ticker(symbol)
        df = t.history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return None
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df.index.name = "date"
        return df.reset_index()

    def _fetch(self, symbol: str, period: str, interval: str):
        df = self.fetch_ohlc(symbol, period, interval)
        if df is None:
            df = self._fetch_public(symbol, period, interval)
        return df
