# Hourly market snapshot → data/snapshots/*.csv
from pathlib import Path
import pandas as pd, numpy as np, math, datetime as dt
import yfinance as yf

OUT = Path("data/snapshots"); OUT.mkdir(parents=True, exist_ok=True)

REGIONS = {
    "na": {
        "indices": ["^GSPC","^NDX","^DJI","^RUT"],
        "bench": "^GSPC",
        "proxy": {"^GSPC":"SPY","^NDX":"QQQ","^DJI":"DIA","^RUT":"IWM"},
        "fxcmd": ["USDCAD=X","USDMXN=X","DXY","CL=F","GC=F","SI=F"],
        "sectors": ["XLK","XLF","XLV","XLE","XLY","XLI","XLU","XLB","XLRE","XLC"],
    },
    "eu": {
        "indices": ["^FTSE","^GDAXI","^FCHI","^STOXX50E"],
        "bench": "^STOXX50E",
        "proxy": {"^FTSE":"EWU","^GDAXI":"EWG","^FCHI":"EWQ","^STOXX50E":"FEZ"},
        "fxcmd": ["EURUSD=X","GBPUSD=X","USDCHF=X","CL=F","BZ=F","GC=F","SI=F"],
        "sectors": [],
    },
    "apac": {
        "indices": ["^N225","^AORD","^HSI","000300.SS"],
        "bench": "^N225",
        "proxy": {"^N225":"EWJ","^AORD":"EWA","^HSI":"2800.HK","000300.SS":"ASHR"},
        "fxcmd": ["USDJPY=X","AUDUSD=X","USDCNY=X","CL=F","GC=F","SI=F","HG=F"],
        "sectors": [],
    },
}

def sma(s, n): return s.rolling(n).mean()
def slope(s): return float(s.iloc[-1] - s.iloc[-5]) / 5.0 if len(s) >= 5 else 0.0
def atr_pct(df, n=14):
    hl=(df["High"]-df["Low"]).abs(); hc=(df["High"]-df["Close"].shift(1)).abs(); lc=(df["Low"]-df["Close"].shift(1)).abs()
    tr=pd.concat([hl,hc,lc],axis=1).max(axis=1); atr=tr.rolling(n).mean()
    return float((atr.iloc[-1]/df["Close"].iloc[-1])*100)

def decision_rule(row):
    above50, above200 = bool(row.get("above_50d")), bool(row.get("above_200d"))
    slope50, rs, atrp, room = row.get("sma50_slope",0.0), row.get("rs",0.0), row.get("atr_pct",0.0), row.get("room_atr",1.2)
    if not above200 or row.get("breadth_50",60) < 35 or (atrp and atrp > 3.0 and rs < 0): return "🔴 Avoid"
    if above50 and above200 and slope50>0 and rs>0 and room>=1.0 and (atrp is None or atrp<=3.0): return "🟢 Trade Today"
    return "🟡 Wait"

def room_to_levels(close, atr=None): return 1.2 if not atr else 1.2

def build_region(key):
    r = REGIONS[key]
    bench = r["bench"]; proxy = r["proxy"]
    syms = list(set(r["indices"]+[bench]+list(proxy.values())+r["fxcmd"]))
    daily = yf.download(syms, period="1y", interval="1d", group_by="ticker", progress=False, threads=False)

    rows=[]
    for sym in r["indices"]:
        src = sym if (isinstance(daily.columns, pd.MultiIndex) and sym in daily.columns.levels[0]) else proxy.get(sym, sym)
        d = daily[src] if isinstance(daily.columns, pd.MultiIndex) else yf.download(src, period="1y", interval="1d", progress=False, threads=False)
        if d is None or d.empty: continue
        close=float(d["Close"].iloc[-1])
        chg1d=float((d["Close"].iloc[-1]/d["Close"].iloc[-2]-1)*100) if len(d)>=2 else 0.0
        chg1w=float((d["Close"].iloc[-1]/d["Close"].iloc[-5]-1)*100) if len(d)>=5 else 0.0
        chg1m=float((d["Close"].iloc[-1]/d["Close"].iloc[-21]-1)*100) if len(d)>=21 else 0.0
        sma50=float(sma(d["Close"],50).iloc[-1]); above50=close>sma50
        sma200=float(sma(d["Close"],200).iloc[-1]) if len(d)>=200 else float("nan"); above200=close>sma200 if sma200==sma200 else False
        slope50=float(slope(sma(d["Close"],50)))
        b = daily[bench] if isinstance(daily.columns, pd.MultiIndex) and bench in daily.columns.levels[0] else yf.download(bench, period="1y", interval="1d", progress=False, threads=False)
        br=float((b["Close"].iloc[-1]/b["Close"].iloc[-5]-1)*100) if b is not None and not b.empty and len(b)>=5 else 0.0
        rs=chg1w-br
        atrp=atr_pct(d) if len(d)>=20 else np.nan
        room=room_to_levels(close, atr=(atrp/100.0*close if atrp==atrp else None))
        rows.append({"symbol": proxy.get(sym, sym), "price": round(close,2), "chg_1d": round(chg1d,2),
                     "chg_1w": round(chg1w,2), "chg_1m": round(chg1m,2), "ytd": "",
                     "above_50d": above50, "above_200d": above200, "sma50_slope": round(slope50,4),
                     "atr_pct": round(atrp,2) if atrp==atrp else "", "rs": round(rs,2),
                     "breadth_50":"", "breadth_200":"", "room_atr": round(room,2), "mom_flag":"", "earnings_window":"", "contras":""})
    df=pd.DataFrame(rows)
    if not df.empty: df["decision"]=df.apply(decision_rule,axis=1)
    df.to_csv(OUT/f"{key}_indices.csv", index=False)

    fx=[]
    for sym in r["fxcmd"]:
        d=yf.download(sym, period="1mo", interval="1d", progress=False, threads=False)
        if d is None or d.empty: continue
        close=float(d["Close"].iloc[-1])
        chg1d=float((d["Close"].iloc[-1]/d["Close"].iloc[-2]-1)*100) if len(d)>=2 else 0.0
        chg1w=float((d["Close"].iloc[-1]/d["Close"].iloc[-5]-1)*100) if len(d)>=5 else 0.0
        fx.append({"symbol": sym, "price": round(close,4), "1D%": round(chg1d,2), "1W%": round(chg1w,2)})
    pd.DataFrame(fx).to_csv(OUT/f"{key}_fxcmd.csv", index=False)

    if r["sectors"]:
        sec=[]
        for sym in r["sectors"]:
            d=yf.download(sym, period="1mo", interval="1d", progress=False, threads=False)
            if d is None or d.empty: continue
            chg1d=float((d["Close"].iloc[-1]/d["Close"].iloc[-2]-1)*100) if len(d)>=2 else 0.0
            sec.append({"sector_etf": sym, "1D%": round(chg1d,2)})
        pd.DataFrame(sec).sort_values("1D%",ascending=False).to_csv(OUT/f"{key}_sectors.csv", index=False)

if __name__ == "__main__":
    for k in ["na","eu","apac"]:
        build_region(k)
    print("Snapshots written → data/snapshots/")
