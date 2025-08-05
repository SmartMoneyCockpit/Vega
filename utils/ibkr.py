"""
Utility functions for Interactive Brokers (IBKR) integration using ib_insync.

The functions in this module attempt to connect to a running IB Gateway or Trader
Workstation instance and fetch live positions and market data.  If the
connection fails or ib_insync is not installed, the module falls back to
placeholder data using yfinance.
"""

from typing import List, Optional

import pandas as pd

try:
    from ib_insync import IB, util, Stock  # type: ignore
except ImportError:
    IB = None  # type: ignore
    util = None  # type: ignore
    Stock = None  # type: ignore

import yfinance as yf


def connect(host: str = "127.0.0.1", port: int = 7497, client_id: int = 1) -> Optional["IB"]:
    """Attempt to connect to IB Gateway or TWS and return an IB instance.

    Parameters
    ----------
    host : str
        IP address of the IBKR gateway.
    port : int
        Port number of the gateway (default 7497 for paper trading, 7496 for live).
    client_id : int
        Unique client identifier.

    Returns
    -------
    ib_insync.IB or None
        A connected IB instance, or `None` if connection fails.
    """
    if IB is None:
        return None
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, readonly=True)
        return ib
    except Exception:
        return None


def get_positions(ib: "IB") -> pd.DataFrame:
    """Return a DataFrame of current positions using the IB instance.

    If no positions are available or if the IB instance is `None`, an empty
    DataFrame is returned.
    """
    if ib is None or IB is None:
        return pd.DataFrame()
    try:
        positions = ib.positions()
        data = []
        for pos in positions:
            contract = pos.contract
            data.append({
                "symbol": contract.symbol,
                "secType": contract.secType,
                "exchange": contract.exchange,
                "currency": contract.currency,
                "position": pos.position,
                "avgCost": pos.avgCost,
            })
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()


def get_live_prices(tickers: List[str]) -> pd.DataFrame:
    """Fetch live prices for a list of tickers using yfinance.

    Although IBKR can provide live quotes, we use yfinance here as a
    non‑authenticated fallback.  Returns a DataFrame with columns `price` and
    `currency`.
    """
    prices = {}
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="1d", interval="1m")
            if not data.empty:
                last_price = data["Close"].iloc[-1]
                prices[ticker] = last_price
        except Exception:
            prices[ticker] = None
    df = pd.DataFrame.from_dict(prices, orient="index", columns=["price"])
    df.index.name = "ticker"
    return df
IBKR Stub for Streamlit Cloud
-----------------------------

This version disables Interactive Brokers connectivity and ensures
the Smart Money Cockpit runs without attempting to open event loops.
Use the full version locally when Trader Workstation (TWS) or IB Gateway is running.
"""

import pandas as pd

# IBKR access disabled in Streamlit Cloud
IB = None
util = None
Stock = None

def connect():
    """Return None to simulate no connection in cloud mode."""
    return None

def get_positions():
    """Return an empty DataFrame as if no positions are held."""
    return pd.DataFrame(columns=["Symbol", "Position", "AvgCost"])

def get_live_price(ticker: str) -> float:
    """Return 0.0 to avoid triggering real-time price checks."""
    return 0.0
