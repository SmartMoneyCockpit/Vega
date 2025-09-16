import os, json, pandas as pd

def _parse_cookies(env_var="TRADINGVIEW_COOKIES"):
    raw = os.getenv(env_var, "").strip()
    if not raw: return None
    try: return json.loads(raw)
    except Exception: return {"raw": raw}

def load_sector_data(country="US", mode="authenticated", refresh_seconds=60):
    sectors = ["Technology","Financials","Healthcare","Energy","Consumer","Industrials","Utilities","Materials","Real Estate","Communication"]
    return pd.DataFrame({"Sector": sectors, "Change%":[0]*len(sectors)})

def render(st, settings):
    st.subheader("Sector Heatmap (TradingView)")
    mode = settings.get("tradingview",{}).get("mode","public")
    cookies_env = settings.get("tradingview",{}).get("cookies_env","TRADINGVIEW_COOKIES")
    cookies = _parse_cookies(cookies_env) if mode=="authenticated" else None
    if mode=="authenticated" and not cookies:
        st.warning("Authenticated mode selected, but no TradingView cookies found; using fallback.")
    df = load_sector_data(mode=mode)
    st.dataframe(df, use_container_width=True)
    st.caption(f"Mode: {mode} | Refresh: {settings.get('tradingview',{}).get('refresh_seconds',60)}s")
