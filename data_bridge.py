import importlib, pandas as pd, streamlit as st
def _try_adapter():
    try: return importlib.import_module('db_adapter')
    except Exception: return None

def get_positions_df():
    a=_try_adapter()
    if a and hasattr(a,'load_positions'):
        try:
            df=a.load_positions()
            if isinstance(df,pd.DataFrame) and not df.empty: return df
        except Exception: pass
    if 'positions_df' in st.session_state and not st.session_state['positions_df'].empty:
        return st.session_state['positions_df']
    return pd.DataFrame({'Ticker':['HPR.TO'],'Qty':[1000],'Avg Cost':[25.0],'Last':[25.4]})

def get_signals_df():
    a=_try_adapter()
    if a and hasattr(a,'load_signals'):
        try:
            df=a.load_signals()
            if isinstance(df,pd.DataFrame) and not df.empty: return df
        except Exception: pass
    if 'signals_df' in st.session_state and not st.session_state['signals_df'].empty:
        return st.session_state['signals_df']
    return pd.DataFrame({'Ticker':['SPY','SPXU','SQQQ','RWM'],'Setup':['Wait','Buy Today','Buy Today','Wait'],'Reason':['Breadth weak','RS flip + options overpriced','NDX RS down','Risk-off fading'],'Country':['USA']*4})

def get_breadth_df():
    a=_try_adapter()
    if a and hasattr(a,'load_breadth'):
        try:
            df=a.load_breadth()
            if isinstance(df,pd.DataFrame) and not df.empty: return df
        except Exception: pass
    if 'breadth_df' in st.session_state and not st.session_state['breadth_df'].empty:
        return st.session_state['breadth_df']
    return pd.DataFrame({'Metric':['VIX','ADV/DEC (NYSE)','%>50DMA (SPX)','%>200DMA (SPX)'],'Value':[18.7,'0.82','47%','62%'],'Status':['Neutral','Risk-Off','Caution','Healthy']})

def get_rs_df():
    a=_try_adapter()
    if a and hasattr(a,'load_rs'):
        try:
            df=a.load_rs()
            if isinstance(df,pd.DataFrame) and not df.empty: return df
        except Exception: pass
    if 'rs_df' in st.session_state and not st.session_state['rs_df'].empty:
        return st.session_state['rs_df']
    return pd.DataFrame({'Bucket':['USA','Canada','Mexico','LATAM ex-MX','Tech','Industrials','Materials','Financials','Staples'],'RS Trend':['🟡','🟡','🟢','🟡','🟠','🟢','🟡','🟡','🟢']})
