
import os
import pandas as pd
from pathlib import Path
from typing import Literal, Tuple, Optional

try:
    import yfinance as yf  # optional at runtime
except Exception:
    yf = None

INTERVAL_MAP = {
    "D": "1d",
    "W": "1wk",
    "M": "1mo",
}

CSV_TEMPLATE = "data/ohlc/{symbol}_{interval}.csv"  # e.g., NASDAQ_QQQ_D.csv


def _heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Return Heikin-Ashi candles from standard OHLCV frame (expects columns: open, high, low, close)."""
    ha = pd.DataFrame(index=df.index.copy())
    ha["close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4.0
    ha["open"] = 0.0
    ha.loc[df.index[0], "open"] = (df["open"].iloc[0] + df["close"].iloc[0]) / 2.0
    for i in range(1, len(df)):
        ha.iat[i, ha.columns.get_loc("open")] = (ha["open"].iat[i-1] + ha["close"].iat[i-1]) / 2.0
    ha["high"] = df[["high", "open", "close"]].max(axis=1)
    ha["low"] = df[["low", "open", "close"]].min(axis=1)
    return ha[["open","high","low","close"]]


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def _bollinger(close: pd.Series, length: int = 20, mult: float = 2.0):
    ma = close.rolling(length).mean()
    sd = close.rolling(length).std()
    upper = ma + mult * sd
    lower = ma - mult * sd
    return ma, upper, lower


def _ichimoku(df: pd.DataFrame, conv:int=9, base:int=26, span:int=52):
    high = df["high"]; low = df["low"]
    conversion = (high.rolling(conv).max() + low.rolling(conv).min()) / 2
    base_line = (high.rolling(base).max() + low.rolling(base).min()) / 2
    span_a = ((conversion + base_line) / 2).shift(base)
    span_b = ((high.rolling(span).max() + low.rolling(span).min()) / 2).shift(base)
    lagging = df["close"].shift(-base)
    return conversion, base_line, span_a, span_b, lagging


def _macd(close: pd.Series, fast:int=12, slow:int=26, signal:int=9):
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    macd = ema_fast - ema_slow
    sig = _ema(macd, signal)
    hist = macd - sig
    return macd, sig, hist


def _rsi(close: pd.Series, length:int=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(length).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(length).mean()
    rs = gain / loss.replace(0, 1e-12)
    return 100 - (100 / (1 + rs))


def _obv(close: pd.Series, volume: pd.Series):
    obv = (volume.where(close > close.shift(1), -volume.where(close < close.shift(1), 0))).fillna(0).cumsum()
    return obv


def _atr(df: pd.DataFrame, length:int=14):
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema9"] = _ema(out["close"], 9)
    out["ema21"] = _ema(out["close"], 21)
    out["ema50"] = _ema(out["close"], 50)
    out["ema200"] = _ema(out["close"], 200)

    bb_mid, bb_up, bb_lo = _bollinger(out["close"], 20, 2.0)
    out["bb_mid"], out["bb_up"], out["bb_lo"] = bb_mid, bb_up, bb_lo

    conv, base, span_a, span_b, lag = _ichimoku(out, 9, 26, 52)
    out["ichimoku_conv"], out["ichimoku_base"], out["ichimoku_a"], out["ichimoku_b"], out["ichimoku_lag"] = conv, base, span_a, span_b, lag

    macd, sig, hist = _macd(out["close"])
    out["macd"], out["macd_sig"], out["macd_hist"] = macd, sig, hist

    out["rsi"] = _rsi(out["close"])
    out["obv"] = _obv(out["close"], out.get("volume", pd.Series(index=out.index, dtype=float)).fillna(0))
    out["atr"] = _atr(out)

    # Heikin Ashi
    ha = _heikin_ashi(out[["open","high","low","close"]])
    out[["ha_open","ha_high","ha_low","ha_close"]] = ha

    return out


def fetch_ohlcv(symbol: str, interval: Literal["D","W","M"]="D", max_points: int = 1500) -> pd.DataFrame:
    """
    Try yfinance; if unavailable or errors, fall back to CSV in data/ohlc.
    Returns a DataFrame with ['time','open','high','low','close','volume'].
    """
    # 1) Try yfinance
    if yf is not None:
        try:
            yf_symbol = symbol.replace(":", "-")  # NASDAQ:QQQ -> NASDAQ-QQQ (yahoo style often just 'QQQ')
            yf_symbol = symbol.split(":")[-1]
            interval_map = INTERVAL_MAP.get(interval, "1d")
            df = yf.download(yf_symbol, period="max", interval=interval_map, auto_adjust=False, progress=False)
            if not df.empty:
                df = df.rename(columns=str.lower)[["open","high","low","close","volume"]].dropna().reset_index()
                df["time"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
                df = df.drop(columns=["date"])
                df = df.tail(max_points).copy()
                df = compute_indicators(df.set_index("time")).reset_index()
                df.rename(columns={"index":"time"}, inplace=True)
                return df
        except Exception:
            pass

    # 2) Fallback CSV
    csv_path = CSV_TEMPLATE.format(symbol=symbol.replace(":","_"), interval=interval)
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}. Provide one or enable yfinance.")
    df = pd.read_csv(csv_path)
    # Expect columns: time, open, high, low, close, volume
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    df = df[["time","open","high","low","close","volume"]].dropna().tail(max_points).copy()
    df = compute_indicators(df.set_index("time")).reset_index()
    df.rename(columns={"index":"time"}, inplace=True)
    return df
