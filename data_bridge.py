import importlib
import pandas as pd
import streamlit as st

def _try_adapter():
    try:
        return importlib.import_module("db_adapter")
    except Exception:
        return None

def get_positions_df():
    adapter = _try_adapter()
    if adapter and hasattr(adapter, "load_positions"):
        try:
            df = adapter.load_positions()
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            pass
    if 'positions_df' in st.session_state and not st.session_state['positions_df'].empty:
        return st.session_state['positions_df']
    return pd.DataFrame({"Ticker":["HPR.TO","ZPR.TO","HSAV.TO"],"Qty":[1000,1000,200],"Avg Cost":[25.00,9.50,29.00],"Last":[25.40,9.55,29.02]})

def get_signals_df():
    adapter = _try_adapter()
    if adapter and hasattr(adapter, "load_signals"):
        try:
            df = adapter.load_signals()
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            pass
    if 'signals_df' in st.session_state and not st.session_state['signals_df'].empty:
        return st.session_state['signals_df']
    return pd.DataFrame({"Ticker":["SPY","SPXU","SQQQ","RWM","SLV","CPER"],"Country":["USA","USA","USA","USA","USA","USA"],"Setup":["Wait","Buy Today","Buy Today","Wait","Watch","Watch"],"Reason":["Breadth weak","RS flip + options overpriced","NDX RS down","Risk-off fading","Trendline test","Copper trendline test"]})

def get_breadth_df():
    adapter = _try_adapter()
    if adapter and hasattr(adapter, "load_breadth"):
        try:
            df = adapter.load_breadth()
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            pass
    if 'breadth_df' in st.session_state and not st.session_state['breadth_df'].empty:
        return st.session_state['breadth_df']
    return pd.DataFrame({"Metric":["VIX","ADV/DEC (NYSE)","%>50DMA (SPX)","%>200DMA (SPX)"],"Value":[18.7,"0.82","47%","62%"],"Status":["Neutral","Risk-Off","Caution","Healthy"]})

def get_rs_df():
    adapter = _try_adapter()
    if adapter and hasattr(adapter, "load_rs"):
        try:
            df = adapter.load_rs()
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            pass
    if 'rs_df' in st.session_state and not st.session_state['rs_df'].empty:
        return st.session_state['rs_df']
    return pd.DataFrame({"Bucket":["USA","Canada","Mexico","LATAM ex-MX","Tech","Industrials","Materials","Financials","Staples"],"RS Trend":["🟡","🟡","🟢","🟡","🟠","🟢","🟡","🟡","🟢"]})
