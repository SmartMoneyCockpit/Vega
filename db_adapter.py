"""db_adapter.py
Wire Vega to your internal database by implementing the stubs below.
"""
from __future__ import annotations
import os
import pandas as pd

# Example (optional): DB_URL = os.getenv("INTERNAL_DB_URL", "")

def load_positions() -> pd.DataFrame:
    """Return columns: Ticker, Qty, Avg Cost, Last"""
    return pd.DataFrame({"Ticker":["HPR.TO","ZPR.TO","HSAV.TO"],"Qty":[1000,1000,200],"Avg Cost":[25.00,9.50,29.00],"Last":[25.40,9.55,29.02]})

def load_signals() -> pd.DataFrame:
    """Return columns: Ticker, Setup, Reason (and optional Country)"""
    return pd.DataFrame({"Ticker":["SPY","SPXU","SQQQ","RWM"],"Setup":["Wait","Buy Today","Buy Today","Wait"],"Reason":["Breadth weak","RS flip + options overpriced","NDX RS down","Risk-off fading"],"Country":["USA","USA","USA","USA"]})

def load_breadth() -> pd.DataFrame:
    """Return columns: Metric, Value, Status"""
    return pd.DataFrame({"Metric":["VIX","ADV/DEC (NYSE)","%>50DMA (SPX)","%>200DMA (SPX)"],"Value":[18.7,"0.82","47%","62%"],"Status":["Neutral","Risk-Off","Caution","Healthy"]})

def load_rs() -> pd.DataFrame:
    """Return columns: Bucket, RS Trend"""
    return pd.DataFrame({"Bucket":["USA","Canada","Mexico","LATAM ex-MX","Tech","Industrials","Materials","Financials","Staples"],"RS Trend":["🟡","🟡","🟢","🟡","🟠","🟢","🟡","🟡","🟢"]})
