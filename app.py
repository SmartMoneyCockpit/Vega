
# app.py — Vega Command Center v1+ (styled)
# Adds: broker fee presets, earnings sync/alerts, broker CSV profiles,
# advanced risk lab (VaR), FX ETF hedge optimizer, options strategy builder,
# quick top nav, and in-app docs. Keeps low-API usage and Render-friendly design.

import os, math, json, io, zipfile, time, statistics as stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import requests

try:
    import yfinance as yf
except Exception:
    yf = None

# ---- Sheets client (import from your local file) ----
from sheets_client import (
    read_config, batch_get, read_range, write_range,
    append_row, append_trade_log, ensure_tab, bootstrap_sheet,
    upsert_config, snapshot_tab
)

APP_VER = "v1.1.5-styled (tabs+themes+keys+cssfix)"

# ---------- Utils ----------
def now(): return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
def rows_to_df(rows):
    rows = rows or []
    if not rows: return pd.DataFrame()
    hdr = [str(c) for c in rows[0]]
    data = [list(r)+[""]*(len(hdr)-len(r)) for r in rows[1:] if any(str(x).strip() for x in r)]
    return pd.DataFrame(data, columns=hdr)
def df_to_rows(df): return [list(df.columns)] + df.fillna("").astype(str).values.tolist()
def col_letter(n):
    s=""; 
    while n: n,r=divmod(n-1,26); s=chr(65+r)+s
    return s or "A"
def _to_float(x, default=0.0):
    try:
        if x is None or str(x).strip()=="" or str(x).lower()=="nan": return default
        return float(x)
    except Exception:
        return default

# ---------- Page Config & Styling ----------
st.set_page_config(page_title="Vega Command Center", layout="wide", page_icon="💹")


# ---- Theme toggle + themable CSS ----
if "vega_theme" not in st.session_state:
    st.session_state["vega_theme"] = "Dark"
theme_choice = st.sidebar.selectbox("Theme", ["Dark","Light"], index=0 if st.session_state["vega_theme"]=="Dark" else 1)
st.session_state["vega_theme"] = theme_choice

def vega_css(theme="Dark"):
    if theme == "Light":
        return """
        <style>
        [data-testid="stAppViewContainer"] { background: #f7fafc !important; }
        [data-testid="stHeader"] { background: #fff !important; border-bottom: 1px solid #e5e7eb !important; }
        .block-container { padding-top: 0.6rem; }
        :root { --vega-primary:#0ea5e9; --vega-accent:#16a34a; --vega-danger:#dc2626; --vega-muted:#475569; }
        .vega-hero { padding:14px 18px; border-radius:12px; background: linear-gradient(90deg, rgba(14,165,233,.10), rgba(22,163,74,.08)); border:1px solid #e5e7eb; color:#0f172a; display:flex; align-items:center; justify-content:space-between; }
        .vega-chips { display:flex; gap:6px; flex-wrap:wrap; }
        .vega-chip { padding:6px 10px; border-radius:999px; font-size:.82rem; border:1px solid #e5e7eb; color:#111827; background:#fff; }
        .vega-chip.active { background: var(--vega-primary); color:#fff; border-color: transparent; }
        .vega-title { font-size:1.1rem; color:#0f172a; margin-top:.6rem; }
        .vega-sep { height:1px; background:#e5e7eb; margin:14px 0; }
        .stTabs [role="tablist"]{margin-top:6px; padding-top:6px;}
.vega-hero{margin-top:8px;}
</style>
        """
    else:
        return """
        <style>
        [data-testid="stAppViewContainer"] { background: #0b1220 !important; }
        [data-testid="stHeader"] { background: transparent !important; border-bottom: 0 !important; }
        .block-container { padding-top: 0.6rem; }
        :root { --vega-primary:#0ea5e9; --vega-accent:#22c55e; --vega-danger:#ef4444; --vega-muted:#64748b; }
        .vega-hero { padding:14px 18px; border-radius:12px; background: linear-gradient(90deg, rgba(14,165,233,.15), rgba(34,197,94,.12)); border:1px solid rgba(148,163,184,.2); color:#e2e8f0; display:flex; align-items:center; justify-content:space-between; }
        .vega-chips { display:flex; gap:6px; flex-wrap:wrap; }
        .vega-chip { padding:6px 10px; border-radius:999px; font-size:.82rem; border:1px solid rgba(148,163,184,.25); color:#cbd5e1; cursor:pointer; }
        .vega-chip.active { background: var(--vega-primary); color:#fff; border-color:transparent; }
        .vega-title { font-size:1.1rem; color:#cbd5e1; margin-top:.6rem; }
        .vega-sep { height:1px; background: rgba(148,163,184,.2); margin:14px 0; }
        [data-testid="stDataFrame"] div[data-baseweb="base-input"] input{ color:#e2e8f0; }
        .stTabs [role="tablist"]{margin-top:6px; padding-top:6px;}
.vega-hero{margin-top:8px;}
</style>
        """

st.markdown(vega_css(st.session_state["vega_theme"]), unsafe_allow_html=True)
# ---- end theme toggle ----


PRIMARY = "#0ea5e9"
ACCENT  = "#22c55e"
DANGER  = "#ef4444"
MUTED   = "#64748b"

st.markdown("""
<style>
/* Global */
:root {{
  --vega-primary: {PRIMARY};
  --vega-accent: {ACCENT};
  --vega-danger: {DANGER};
  --vega-muted: {MUTED};
}}
html, body {{ background: #0b1220; }}
section.main > div {{ padding-top: 0.6rem; }}

.vega-title {{
  font-size: 1.1rem;
  color: #cbd5e1;
  margin-top: .6rem;
}}

.vega-hero {{
  padding: 14px 18px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(14,165,233,.15), rgba(34,197,94,.12));
  border: 1px solid rgba(148,163,184,.2);
  color: #e2e8f0;
  display:flex; align-items:center; justify-content:space-between;
}}
.vega-hero .brand {{
  font-weight: 700; font-size: 1.05rem; letter-spacing:.3px;
}}
.vega-chips {{ display:flex; gap:6px; flex-wrap: wrap; }}
.vega-chip {{
  padding: 6px 10px; border-radius: 999px; font-size:.82rem;
  border: 1px solid rgba(148,163,184,.25); color:#cbd5e1; cursor:pointer;
}}
.vega-chip.active {{ background: var(--vega-primary); color: white; border-color: transparent; }}
.vega-card {{
  background: rgba(2,6,23,.5); border: 1px solid rgba(148,163,184,.2);
  border-radius: 12px; padding: 14px 14px; color:#e2e8f0;
}}
.vega-sep {{ height:1px; background: rgba(148,163,184,.2); margin: 14px 0; }}
/* table contrast */
[data-testid="stDataFrame"] div[data-baseweb="base-input"] input{{ color:#e2e8f0; }}
.stTabs [role="tablist"]{margin-top:6px; padding-top:6px;}
.vega-hero{margin-top:8px;}
</style>
""", unsafe_allow_html=True)

# ---------- Config ----------
CFG = {}
for r in read_config() or []:
    if not r: continue
    if len(r)>=2 and r[0] and "=" not in str(r[0]): CFG[str(r[0]).strip()] = str(r[1]).strip()
    else:
        c = str(r[0]).strip()
        if "=" in c: k,v = c.split("=",1); CFG[k.strip()] = v.strip()

POLY      = os.getenv("POLYGON_KEY")
NEWSKEY   = os.getenv("NEWSAPI_KEY")
ADMIN_PIN = os.getenv("ADMIN_PIN") or CFG.get("ADMIN_PIN","")

ALERT_PCT = float(CFG.get("ALERT_PCT", os.getenv("ALERT_PCT","1.5")))
RR_TARGET = float(CFG.get("RR_TARGET", os.getenv("RR_TARGET","2.0")))

# Fallback fees (can be overridden by presets)
FEES_BASE     = float(CFG.get("FEES_BASE", "0"))
FEES_BPS_BUY  = float(CFG.get("FEES_BPS_BUY", "0"))
FEES_BPS_SELL = float(CFG.get("FEES_BPS_SELL", "0"))
FEES_TAXBPS   = float(CFG.get("FEES_TAXBPS", "0"))

APAC_COUNTRIES = [s.strip() for s in (CFG.get("APAC_COUNTRIES","JP,AU,HK,SG,IN").split(",")) if s.strip()]
NA_COUNTRIES   = [s.strip() for s in (CFG.get("NA_COUNTRIES","US,CA").split(",")) if s.strip()]
SUFFIX = {
    "JP": CFG.get("SUFFIX_JP",".T"),
    "AU": CFG.get("SUFFIX_AU",".AX"),
    "NZ": CFG.get("SUFFIX_NZ",".NZ"),
    "HK": CFG.get("SUFFIX_HK",".HK"),
    "SG": CFG.get("SUFFIX_SG",".SI"),
    "IN": CFG.get("SUFFIX_IN",".NS"),
}

# ---------- Sidebar ----------
st.sidebar.header("Vega • Session Controls")
entered_pin = st.sidebar.text_input("Admin PIN (optional)", type="password", help="Only required if you set ADMIN_PIN in Config.")
is_admin = (not ADMIN_PIN) or (entered_pin and entered_pin == ADMIN_PIN)

if st.sidebar.button("Setup / Repair Google Sheet"):
    try: bootstrap_sheet(); st.sidebar.success("Core tabs checked/created.")
    except Exception as e: st.sidebar.error(f"Bootstrap error: {e}")

with st.sidebar.expander("Diagnostics"):
    st.write({"version": APP_VER, "POLYGON": bool(POLY), "NEWSAPI": bool(NEWSKEY), "ADMIN": bool(ADMIN_PIN)})

# ---------- Price helpers ----------
def price_polygon(sym: str):
    if not POLY: return None
    try:
        r = requests.get(
            f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{sym.upper()}",
            params={"apiKey": POLY}, timeout=5)
        if r.status_code!=200: return None
        j=r.json(); return float(j.get("ticker",{}).get("lastTrade",{}).get("p") or 0) or None
    except Exception: return None

def price_yf(sym: str):
    if yf is None: return None
    try:
        t = yf.Ticker(sym); hist = t.history(period="1d")
        if not hist.empty: return float(hist["Close"].iloc[-1])
    except Exception: return None
    return None

def apply_suffix(ticker: str, country: str) -> str:
    tk = str(ticker or "").strip()
    if "." in tk: return tk
    sfx = SUFFIX.get(country.upper()); return tk + sfx if sfx else tk

def get_price(sym: str, region: str="NA", country: str="US"):
    if region=="NA": return price_polygon(sym) or price_yf(sym)
    return price_yf(apply_suffix(sym, country))

def is_market_open(region: str):
    now_utc = datetime.utcnow()
    wd = now_utc.weekday()
    if wd>=5: return False
    if region=="NA":
        month = now_utc.month
        if 3<=month<=11: start, end = 13*60+30, 20*60
        else:            start, end = 14*60+30, 21*60
        mins = now_utc.hour*60 + now_utc.minute
        return start <= mins <= end
    else:
        mins = now_utc.hour*60 + now_utc.minute
        return 0 <= mins <= 360

# ---------- Core data helpers ----------
def ensure_tabs(map_name_to_headers: Dict[str, List[str]]):
    for tab, headers in map_name_to_headers.items(): ensure_tab(tab, headers)
def read_df(a1): return rows_to_df(read_range(a1))
def save_df(tab, df, audit_note: str = None):
    if "Audit" in df.columns and audit_note:
        df = df.copy(); df.loc[:, "Audit"] = audit_note
    rows = df_to_rows(df); m = len(rows[0]) if rows else 1; n = max(1,len(rows))
    write_range(f"{tab}!A1:{col_letter(m)}{n}", rows)

# ---------- Watchlist alert columns ----------
def badges(row, alert=1.5):
    tags = []
    try:
        if str(row.get("Δ% to Entry","")) not in ("", "nan") and str(row.get("Entry","")) not in ("", "nan"):
            d = float(row["Δ% to Entry"])
            if abs(d) <= alert: tags.append("🟩 near-entry")
            elif d < -alert:    tags.append("🟠 below")
            elif d > alert:     tags.append("🔵 extended")
        if str(row.get("R to Stop","")) not in ("", "nan") and float(row["R to Stop"]) < -0.2:
            tags.append("🟥 risk")
        if "R to Target" in row and str(row.get("R to Target","")) not in ("", "nan") and float(row["R to Target"])<=0.2:
            tags.append("🎯 target")
    except Exception:
        pass
    return " | ".join(tags)

def compute_alert_cols(df, region="NA"):
    if df.empty or "Ticker" not in df.columns: return df
    df = df.copy()
    prices = []
    for i in range(len(df)):
        sym = str(df.at[i, "Ticker"]).strip()
        c   = str(df.at[i, "Country"]) if "Country" in df.columns else ("US" if region=="NA" else "JP")
        p = get_price(sym, region=region, country=c) if is_market_open(region) else None
        prices.append(p)
    df["Price"] = prices
    for c in ("Entry","Stop","Target"):
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Entry" in df.columns:
        df["Δ% to Entry"] = ((df["Price"]-df["Entry"])/df["Entry"]*100).round(2)
    if "Stop" in df.columns and "Entry" in df.columns:
        base = (df["Entry"]-df["Stop"]).replace(0, pd.NA)
        df["R to Stop"] = ((df["Price"]-df["Entry"])/base).round(2)
    if "Target" in df.columns and "Stop" in df.columns:
        base = (df["Entry"]-df["Stop"]).replace(0, pd.NA)
        df["R to Target"] = ((df["Target"]-df["Price"])/base).round(2)
    df["Badges"] = df.apply(lambda r: badges(r, alert=ALERT_PCT), axis=1)
    return df

# ---------- TradeLog: fees, partials, FIFO/LIFO/AVG, tags ----------
def ensure_log_columns(tab_name: str):
    needed = ["ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"]
    hdr = read_range(f"{tab_name}!1:1"); hdr = hdr[0] if hdr else []
    if not hdr: return
    changed = False
    for c in needed:
        if c not in hdr: hdr.append(c); changed=True
    if changed:
        write_range(f"{tab_name}!A1:{col_letter(len(hdr))}1", [hdr])

def header_map(tab_name: str) -> Dict[str,int]:
    row = read_range(f"{tab_name}!1:1"); hdr = row[0] if row else []
    return {str(h).strip(): i+1 for i,h in enumerate(hdr)}  # 1-based

def list_open_lots(log_df: pd.DataFrame, symbol: str) -> List[Tuple[int,float,str,float,str]]:
    out = []
    if log_df.empty: return out
    df = log_df.copy()
    for c in ("Qty","ExitQty","Price"):
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    m = (df.get("Symbol","").astype(str)==symbol)
    for idx, r in df[m].iterrows():
        qty = float(r.get("Qty",0) or 0)
        exq = float(r.get("ExitQty",0) or 0)
        remain = max(qty - exq, 0.0)
        if remain>0 and str(r.get("Side","")).upper() in ("BUY","SELL"):
            out.append((idx, remain, str(r.get("Side","")).upper(), float(r.get("Price",0) or 0), str(r.get("Timestamp",""))))
    return out

# ---- Fee presets (Fee_Presets tab) ----
def load_fee_presets():
    ensure_tabs({"Fee_Presets": ["Preset","Markets","Base","BpsBuy","BpsSell","TaxBps","Notes"]})
    return read_df("Fee_Presets!A1:Z200")

def match_preset_for(country_code: str, preset_name: str=None):
    df = load_fee_presets()
    if not df.empty and preset_name:
        z = df[df["Preset"].astype(str)==preset_name]
        if not z.empty:
            r = z.iloc[0]
            return float(_to_float(r.get("Base",0))), float(_to_float(r.get("BpsBuy",0))), float(_to_float(r.get("BpsSell",0))), float(_to_float(r.get("TaxBps",0)))
    # match by country in Markets list
    if not df.empty:
        for _, r in df.iterrows():
            mkts = [s.strip().upper() for s in str(r.get("Markets","")).split(",") if s.strip()]
            if country_code.upper() in mkts:
                return float(_to_float(r.get("Base",0))), float(_to_float(r.get("BpsBuy",0))), float(_to_float(r.get("BpsSell",0))), float(_to_float(r.get("TaxBps",0)))
    # fallback to globals
    return FEES_BASE, FEES_BPS_BUY, FEES_BPS_SELL, FEES_TAXBPS

def _calc_fees(side: str, exit_price: float, qty: float, base: float, bps_buy: float, bps_sell: float, taxbps: float=0.0) -> float:
    bps = bps_buy if side=="BUY" else bps_sell
    fee = float(base) + (bps/10000.0)*(exit_price*qty)
    fee += (taxbps/10000.0)*(exit_price*qty)
    return fee

def update_tradelog_pnl(tab_name: str, log_df: pd.DataFrame, watch_df: pd.DataFrame):
    if log_df.empty: return
    ensure_log_columns(tab_name)
    hmap = header_map(tab_name)
    n = len(log_df) + 1  # incl header
    # map of symbol->stop / country for fees + R
    stop_map, country_map = {}, {}
    if not watch_df.empty and "Ticker" in watch_df.columns:
        if "Stop" in watch_df.columns:
            try:
                stop_map = pd.to_numeric(watch_df.set_index("Ticker")["Stop"], errors="coerce").to_dict()
            except Exception: pass
        if "Country" in watch_df.columns:
            country_map = watch_df.set_index("Ticker")["Country"].to_dict()
    pnl_vals, r_vals = [], []
    for _, r in log_df.iterrows():
        try:
            side = str(r.get("Side","BUY")).upper()
            qty  = _to_float(r.get("Qty",0), 0.0)
            exq  = _to_float(r.get("ExitQty",0), 0.0)
            close_qty = exq if exq>0 else (qty if str(r.get("ExitPrice","")).strip()!="" else 0.0)
            if close_qty<=0:
                pnl_vals.append(""); r_vals.append(""); continue
            px   = _to_float(r.get("Price",0), 0.0)
            ex   = _to_float(r.get("ExitPrice",0), px)
            fees = _to_float(r.get("Fees",0), 0.0)  # already includes tax if any
            pnl_raw = (ex - px)*close_qty if side=="BUY" else (px - ex)*close_qty
            pnl = pnl_raw - fees
            pnl_vals.append(round(pnl,2))
            sym  = str(r.get("Symbol",""))
            stop = float(stop_map.get(sym, float("nan")))
            if not math.isnan(stop) and px!=stop:
                R = (ex - px)/(px - stop) if side=="BUY" else (px - ex)/(stop - px)
                r_vals.append(round(R,2))
            else:
                r_vals.append("")
        except Exception:
            pnl_vals.append(""); r_vals.append("")
    if "PnL" in hmap:
        col = col_letter(hmap["PnL"]); write_range(f"{tab_name}!{col}2:{col}{n}", [[x] for x in pnl_vals])
    if "R" in hmap:
        col = col_letter(hmap["R"]); write_range(f"{tab_name}!{col}2:{col}{n}", [[x] for x in r_vals])

def set_row_values(tab_name: str, rownum: int, updates: Dict[str, float]):
    hmap = header_map(tab_name)
    for k,v in updates.items():
        if k in hmap:
            col = col_letter(hmap[k]); write_range(f"{tab_name}!{col}{rownum}:{col}{rownum}", [[v]])

def close_single_lot(tab_name: str, log_df: pd.DataFrame, idx: int, exit_price: float, exit_qty: float, fees: float):
    rownum = idx + 2
    r = log_df.loc[idx]
    cur_exq = _to_float(r.get("ExitQty",0), 0.0)
    cur_fees= _to_float(r.get("Fees",0), 0.0)
    updates = {"ExitPrice": exit_price, "ExitQty": cur_exq + exit_qty, "Fees": cur_fees + fees}
    set_row_values(tab_name, rownum, updates)

def close_allocate(tab_name: str, lots: List[Tuple[int,float,str,float,str]], mode: str, exit_price: float, exit_qty: float, side_hint: str, fee_tuple=(0,0,0,0)):
    if not lots: return "No open lots."
    base,bpb,bps,taxbps = fee_tuple
    total_remain = sum(q for _,q,_,_,_ in lots)
    if exit_qty<=0 or total_remain<=0: return "Nothing to close."
    if exit_qty > total_remain: exit_qty = total_remain
    # choose order
    if mode=="FIFO":  lots_sorted = sorted(lots, key=lambda x: x[4])
    elif mode=="LIFO": lots_sorted = sorted(lots, key=lambda x: x[4], reverse=True)
    elif mode=="Average": lots_sorted = sorted(lots, key=lambda x: x[1], reverse=True)
    else: lots_sorted = lots[:]
    remaining = exit_qty
    for (idx, rem, side, px, ts) in lots_sorted:
        if remaining<=0: break
        part = min(rem, exit_qty * (rem/total_remain)) if mode=="Average" else min(rem, remaining)
        if part<=0: continue
        fees = _calc_fees(side_hint or side, exit_price, part, base, bpb, bps, taxbps)
        close_single_lot(tab_name, log_df, idx, exit_price, part, fees)
        remaining -= part
    return "Closed."

# ---------- Positions dash ----------
def positions_dashboard(log_df: pd.DataFrame, watch_df: pd.DataFrame, region="NA", tag_filter=None):
    if log_df.empty: st.info("No trades yet."); return
    df = log_df.copy()
    for c in ("Qty","Price","ExitPrice","ExitQty","PnL"):
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    if tag_filter:
        def has_tag(x):
            s = str(x or "").lower()
            return any(t.lower() in s for t in tag_filter)
        df = df[df.get("Tags","").apply(has_tag)]
    realized = float(pd.to_numeric(df.get("PnL", pd.Series([])), errors="coerce").fillna(0).sum()) if "PnL" in df.columns else 0.0
    open_pnl = 0.0
    for _, r in df.iterrows():
        try:
            qty = float(r.get("Qty",0) or 0); exq = float(r.get("ExitQty",0) or 0)
            remain = max(qty - exq, 0.0)
            if remain<=0: continue
            side = str(r.get("Side","BUY")).upper()
            px   = float(r.get("Price",0) or 0); sym = str(r.get("Symbol",""))
            pr   = get_price(sym, region=region) or px
            pnl  = (pr - px)*remain if side=="BUY" else (px - pr)*remain
            open_pnl += pnl
        except Exception: pass
    realized_df = df[pd.to_numeric(df.get("PnL", pd.Series([])), errors="coerce").notna()]
    wins = int((realized_df["PnL"]>0).sum()) if not realized_df.empty else 0
    trades = int(len(realized_df)) if not realized_df.empty else 0
    Rs = []
    if "R" in realized_df.columns:
        for x in realized_df["R"]:
            try:
                if str(x) not in ("","nan"): Rs.append(float(x))
            except Exception: pass
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Realized P/L", f"${realized:,.0f}")
    c2.metric("Open P/L", f"${open_pnl:,.0f}")
    wr = (wins/trades*100) if trades else 0.0
    c3.metric("Win %", f"{wr:.0f}%")
    avgR = (sum(Rs)/len(Rs)) if Rs else 0.0
    c4.metric("Avg R (closed)", f"{avgR:.2f}")

# ---------- Earnings sync ----------
def earnings_snapshot(tickers: List[str]):
    out = []
    if yf is None: return out
    for tkr in tickers[:60]:
        try:
            t = yf.Ticker(tkr)
            cal = None
            try:
                cal = t.get_earnings_dates(limit=1)
                nextE = str(cal.index[0].date()) if (cal is not None and not cal.empty) else ""
            except Exception:
                nextE = ""
            out.append({"Ticker": tkr, "NextEarnings": nextE})
        except Exception:
            out.append({"Ticker": tkr, "NextEarnings": ""})
    return out

# ---------- Cockpit (NA / APAC) ----------
def cockpit(region_name, watch_tab, log_tab, countries, region_code="NA"):
    ensure_tabs({
        watch_tab: ["Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit"],
        log_tab:   ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"],
        "Fee_Presets": ["Preset","Markets","Base","BpsBuy","BpsSell","TaxBps","Notes"]
    })
    wrows, lrows = batch_get([f"{watch_tab}!A1:Z2000", f"{log_tab}!A1:Z8000"])
    wdf, ldf = rows_to_df(wrows), rows_to_df(lrows)

    try:
        update_tradelog_pnl(log_tab, ldf, wdf)
        ldf = rows_to_df(read_range(f"{log_tab}!A1:Z8000"))
    except Exception as e:
        st.warning(f"PnL auto-calc: {e}")

    st.markdown("""
    <div class="vega-hero">
      <div class="brand">Vega • {region_name} — {"OPEN" if is_market_open(region_code) else "CLOSED"}</div>
      <div class="vega-chips">
        <span class="vega-chip">ALERT_PCT {ALERT_PCT}</span>
        <span class="vega-chip">RR_TARGET {RR_TARGET}</span>
        <span class="vega-chip">v{APP_VER}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    wdfA = compute_alert_cols(wdf, region=region_code)
    st.markdown('<div class="vega-title">Watch List</div>', unsafe_allow_html=True)
    st.dataframe(wdfA, use_container_width=True, hide_index=True)

    # Earnings alerts (on-demand)
    if st.button("Sync earnings (on-demand)", key=f"sync_{region_code}"):
        tickers = wdfA["Ticker"].astype(str).tolist() if "Ticker" in wdfA.columns else []
        snap = earnings_snapshot(tickers)
        if snap:
            ensure_tabs({"Earnings": ["Timestamp","Ticker","NextEarnings"]})
            for r in snap:
                append_row("Earnings", [now(), r["Ticker"], r["NextEarnings"]])
            st.success("Earnings snapshot appended to 'Earnings' tab.")
    soon = []
    try:
        e = read_df("Earnings!A1:Z5000")
        if not e.empty:
            e["Days"] = pd.to_datetime(e["NextEarnings"], errors="coerce") - pd.Timestamp.utcnow().normalize()
            soon = e[e["Days"].dt.days.between(0,7, inclusive="both")]
    except Exception: pass
    if isinstance(soon, pd.DataFrame) and not soon.empty:
        st.info("Upcoming earnings in ≤ 7 days:")
        st.dataframe(soon[["Ticker","NextEarnings"]], use_container_width=True, hide_index=True)

    # Dashboard
    with st.expander("Positions dashboard", expanded=False):
        tags_present = sorted({t.strip() for t in (",".join(ldf.get("Tags","").astype(str).tolist())).split(",") if t.strip()})
        filt = st.multiselect("Filter by tag(s)", tags_present, default=[])
        positions_dashboard(ldf, wdfA, region=region_code, tag_filter=filt)

    st.markdown('<div class="vega-sep"></div>', unsafe_allow_html=True)
    st.subheader("Close Trade / Partials")
    # build open symbol list
    open_syms = []
    if not ldf.empty:
        tmp = ldf.copy()
        for c in ("Qty","ExitQty"):
            if c in tmp.columns: tmp[c] = pd.to_numeric(tmp[c], errors="coerce")
        tmp["Remain"] = tmp.get("Qty",0).fillna(0) - tmp.get("ExitQty",0).fillna(0)
        open_syms = sorted(tmp.loc[tmp["Remain"]>0, "Symbol"].dropna().astype(str).unique().tolist())
    mode = st.radio("Mode", ["Single lot", "Average", "FIFO", "LIFO"], horizontal=True)
    fee_df = load_fee_presets(); presets = ["<auto-match>"] + fee_df.get("Preset", pd.Series([])).astype(str).tolist()
    preset_choice = st.selectbox("Broker fee preset", presets, index=0, help="Choose a preset or let the app match by market/country.")
    if open_syms:
        c1,c2,c3 = st.columns([2,1.1,1])
        sym = c1.selectbox("Symbol (open)", open_syms, index=0, key=f"ct_sym_{log_tab}")
        px0 = get_price(sym, region=region_code) or 0.0
        ex  = c2.number_input("ExitPrice", 0.0, 1e9, float(px0), format="%.4f", key=f"ct_px_{log_tab}")
        auto_fee = c3.checkbox("Auto fees", value=True)
        lots = list_open_lots(ldf, sym)
        total_remain = sum(q for _,q,_,_,_ in lots)

        # determine fee tuple (base,bpb,bps,taxbps)
        country = ""
        try:
            if "Country" in wdfA.columns:
                country = str(wdfA.loc[wdfA["Ticker"].astype(str)==sym, "Country"].iloc[0])
        except Exception: country="US"
        fee_tuple = match_preset_for(country, None if preset_choice=="<auto-match>" else preset_choice)

        if mode=="Single lot":
            labels = []
            for (idx, rem, side, px, ts) in lots:
                tid = str(ldf.at[idx, "TradeID"]) if "TradeID" in ldf.columns else f"row{idx+2}"
                labels.append(f"{tid} | {side} | remain={rem:g} @ {px:g}")
            if not labels: st.info("No open lots."); return
            i = st.selectbox("Choose lot", list(range(len(lots))), format_func=lambda j: labels[j])
            _, remain, side, px, _ = lots[i]
            c4,c5 = st.columns([1,1])
            q  = c4.number_input("ExitQty", 0.0, float(remain), float(remain), format="%.4f")
            fee = _calc_fees(side, ex, q, *fee_tuple) if auto_fee else c5.number_input("Fees (this close)", 0.0, 1e9, 0.0, format="%.2f")
            if st.button("Close selected lot", key=f"close1_{log_tab}"):
                close_single_lot(log_tab, ldf, lots[i][0], ex, q, fee)
                update_tradelog_pnl(log_tab, rows_to_df(read_range(f"{log_tab}!A1:Z8000")), wdf)
                st.success("Closed.")
        else:
            if total_remain<=0: st.info("No open lots to close.")
            else:
                c4,c5 = st.columns([1,1])
                q  = c4.number_input("ExitQty (bulk)", 0.0, float(total_remain), float(total_remain), format="%.4f")
                fee_total = _calc_fees(lots[0][2] if lots else "BUY", ex, q, *fee_tuple) if auto_fee else c5.number_input("Total fees", 0.0, 1e9, 0.0, format="%.2f")
                msg = close_allocate(log_tab, lots, mode, ex, q, lots[0][2] if lots else "BUY", fee_tuple if auto_fee else (0,0,0,0))
                # Allocate manual fees proportionally
                if not auto_fee and fee_total>0:
                    remaining = q; total2 = sum(rem for _,rem,_,_,_ in lots)
                    for (idx, rem, side, px, ts) in lots:
                        if remaining<=0: break
                        part = min(rem, q*(rem/total2)) if mode=="Average" else min(rem, remaining)
                        if part<=0: continue
                        rownum = idx + 2
                        cur = rows_to_df(read_range(f"{log_tab}!A{rownum}:Z{rownum}"))
                        cur_fee = _to_float(cur.get("Fees",[0]).iloc[0] if not cur.empty and "Fees" in cur.columns else 0.0, 0.0)
                        add = fee_total * (part/q) if q>0 else 0.0
                        set_row_values(log_tab, rownum, {"Fees": cur_fee + add, "ExitPrice": ex})
                        remaining -= part
                update_tradelog_pnl(log_tab, rows_to_df(read_range(f"{log_tab}!A1:Z8000")), wdf)
                st.success(msg)

    # Quick Entry + tags
    st.markdown('<div class="vega-sep"></div>', unsafe_allow_html=True)
    st.subheader(f"Quick Entry → {log_tab}")
    tickers = wdf["Ticker"].astype(str).tolist() if "Ticker" in wdf.columns else ["SPY"]
    with st.form(f"form_{log_tab}", clear_on_submit=True):
        c1,c2,c3,c4,c5,c6,c7 = st.columns([2,1,1,1,1.6,3,2])
        sym = c1.selectbox("Symbol", tickers, index=0)
        side= c2.selectbox("Side", ["BUY","SELL"]) 
        qty = c3.number_input("Qty", 1.0, 1_000_000.0, 1.0, step=1.0, format="%.4f")
        country = c4.selectbox("Country", countries, index=0)
        px0 = get_price(sym, region=region_code, country=country) or 0.0
        prc = c5.number_input("Price (opt)", 0.0, 1e9, float(px0), format="%.4f")
        note= c6.text_input("Note")
        tags= c7.text_input("Tags (comma)")
        ok  = st.form_submit_button("Append")
        if ok:
            tid = f"{sym}-{int(time.time())}"
            audit = f"{now()}|{APP_VER}|{region_name}"
            row = [now(), tid, sym.upper(), side, qty, prc, note, "", "", "", "", "", tags, audit]
            append_trade_log(row, tab_name=log_tab); st.success(f"Logged {sym} x{qty:g} ({side})")    

# ---------- Risk Lab (VaR) ----------
def page_risk_lab():
    st.subheader("Risk Lab — 1‑day Parametric VaR (95%)")
    st.caption("Estimates using last 60 trading days of returns; assumes normality. Use for guidance only.")
    syms = st.text_input("Symbols (comma)", value="SPY,AAPL,MSFT").replace(" ","").split(",")
    eq   = st.number_input("Account equity ($)", 0.0, 1e12, _to_float(CFG.get("ACCOUNT_EQUITY","100000"),100000.0), step=1000.0)
    wts  = st.text_input("Weights (comma, sum=1)", value="0.34,0.33,0.33").replace(" ","").split(",")
    try:
        w = np.array([float(x) for x in wts]); w = w/np.sum(w)
    except Exception:
        st.error("Weights parse error."); return
    if yf is None:
        st.warning("yfinance not available on server."); return
    # pull history
    prices = {}
    for s in syms:
        try:
            t = yf.Ticker(s); h = t.history(period="3mo")["Close"].pct_change().dropna()
            if not h.empty: prices[s] = h.tail(60)
        except Exception: pass
    if len(prices)<2: st.warning("Not enough return data."); return
    R = pd.DataFrame(prices).dropna()
    cov = np.cov(R.values.T)
    port_var = np.sqrt(w @ cov @ w)  # daily sigma
    VaR = 1.65 * port_var * eq  # 95%
    st.metric("Estimated 1‑day VaR (95%)", f"${VaR:,.0f}")
    st.caption("Interpretation: 1-day loss should exceed this amount only ~5% of days under model assumptions.")

# ---------- Options Strategy Builder ----------
def N(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def bs_greeks(S, K, T, r, sigma, kind="call"):
    if T<=0 or sigma<=0: return {"delta":0,"gamma":0,"theta":0,"vega":0}
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T)/(sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    if kind=="call":
        delta = N(d1)
    else:
        delta = N(d1)-1
    gamma = math.exp(-0.5*d1*d1)/(S*sigma*math.sqrt(2*math.pi*T))
    vega  = S*math.exp(-0.5*d1*d1)*math.sqrt(T)/math.sqrt(2*math.pi)
    theta = -(S*math.exp(-0.5*d1*d1)*sigma)/(2*math.sqrt(2*math.pi*T)) - (r*K*math.exp(-r*T))*N(d2 if kind=="call" else -d2)
    return {"delta":delta,"gamma":gamma,"theta":theta,"vega":vega}

def page_options_builder():
    st.subheader("Options Strategy Builder (multi‑leg)")
    tkr = st.text_input("Underlying", value="SPY")
    r   = st.number_input("Risk‑free rate", 0.0, 0.2, 0.05, 0.005)
    if yf is None:
        st.warning("yfinance not available for chains; manual inputs only."); return
    t = yf.Ticker(tkr)
    exps = t.options
    if not exps: st.warning("No options data."); return
    exp = st.selectbox("Expiration", exps, index=0)
    chain = t.option_chain(exp)
    st.caption("Add legs (positive = long, negative = short). Greeks from Black‑Scholes using IV in chain.")
    legs = []
    with st.form("legs"):
        for i in range(1, 5):
            st.markdown(f"**Leg {i}**")
            typ = st.selectbox(f"Type {i}", ["call","put"], key=f"type{i}")
            strike = st.selectbox(f"Strike {i}", sorted(set(chain.calls["strike"].tolist()+chain.puts["strike"].tolist())), key=f"strike{i}")
            qty = st.number_input(f"Qty {i} (±)", -50, 50, 0, key=f"qty{i}")
            legs.append((typ, float(strike), int(qty)))
        ok = st.form_submit_button("Compute Greeks")
    if ok:
        S = float(t.history(period="1d")["Close"].iloc[-1])
        T = max((datetime.fromisoformat(exp)+" 00:00" if " " in exp else datetime.fromisoformat(exp+" 00:00")).timestamp() - time.time(), 0)/ (365*24*3600)
        gtot = {"delta":0,"gamma":0,"theta":0,"vega":0}
        for typ,K,q in legs:
            if q==0: continue
            # get IV from the chain
            df = chain.calls if typ=="call" else chain.puts
            row = df.loc[df["strike"]==K].head(1)
            iv = float(row["impliedVolatility"].iloc[0]) if not row.empty and "impliedVolatility" in row.columns else 0.2
            g = bs_greeks(S,K,T,r,iv,kind=typ)
            for k in gtot: gtot[k] += g[k]*q
        st.write("**Net Greeks (per 1 underlying unit):**", {k: round(v,3) for k,v in gtot.items()})

# ---------- Broker Import (profiles) ----------
PROFILES = {
    "Interactive Brokers (trades.csv)": {"Timestamp":"Date/Time","Symbol":"Symbol","Side":"Buy/Sell","Qty":"Quantity","Price":"TradePrice","Note":"Code"},
    "Tastytrade": {"Timestamp":"Trade Date","Symbol":"Symbol","Side":"Action","Qty":"Quantity","Price":"Price","Note":"Description"},
    "Fidelity": {"Timestamp":"Run Date","Symbol":"Security","Side":"Action","Qty":"Quantity","Price":"Price","Note":"Details"}
}
def page_broker_import():
    st.subheader("Broker Import → TradeLog")
    region = st.radio("Target region", ["NA","APAC"], horizontal=True)
    log_tab = "NA_TradeLog" if region=="NA" else "APAC_TradeLog"
    ensure_tabs({log_tab: ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"]})
    prof = st.selectbox("Profile", ["Custom"] + list(PROFILES.keys()))
    f = st.file_uploader("Upload CSV", type=["csv"])
    if not f: return
    df = pd.read_csv(f)
    st.write("Columns detected:", list(df.columns))
    mapping = {}
    if prof!="Custom":
        mapping = PROFILES[prof]
        st.info("Using profile defaults. You can adjust below if needed.")
    fields = ["Timestamp","Symbol","Side","Qty","Price","Note"]
    cols = list(df.columns)
    for k in fields:
        mapping[k] = st.selectbox(k, ["<none>"]+cols, index=(cols.index(mapping[k]) + 1) if (prof!="Custom" and mapping[k] in cols) else 0, key=f"map_{k}")
    if st.button("Append rows"):
        out = []
        for _, r in df.iterrows():
            vals = {}
            for k in fields:
                col = mapping.get(k, "<none>")
                vals[k] = (r[col] if col!="<none>" and col in r else "")
            tid = f"{vals['Symbol']}-{int(time.time())}"
            row = [str(vals["Timestamp"] or now()), tid, str(vals["Symbol"]).upper(), str(vals["Side"]).upper(), _to_float(vals["Qty"],0.0), _to_float(vals["Price"],0.0), str(vals["Note"] or ""), "", "", "", "", "", "", f"{now()}|{APP_VER}|IMPORT"]
            out.append(row)
        for row in out: append_trade_log(row, tab_name=log_tab)
        st.success(f"Appended {len(out)} rows to {log_tab}.")

# ---------- FX & Hedges (ETF optimizer) ----------
FX_PAIRS = {"EUR":"EURUSD=X","JPY":"JPY=X","GBP":"GBPUSD=X","CAD":"CADUSD=X","AUD":"AUDUSD=X","CHF":"CHFUSD=X","MXN":"MXNUSD=X","HKD":"HKDUSD=X","SGD":"SGDUSD=X","INR":"INR=X"}
ETF_HINT = {"EUR":"FXE","JPY":"FXY","GBP":"FXB","CAD":"FXC","AUD":"FXA","CHF":"FXF"}

def fx_rate(code: str):
    if yf is None: return None
    try:
        t = yf.Ticker(code); hist = t.history(period="1d")
        if not hist.empty: return float(hist["Close"].iloc[-1])
    except Exception: return None
    return None

def hedge_via_etf(currency: str, exposure_usd: float, target_pct: float=1.0, slippage_bps: float=5.0):
    pair = FX_PAIRS.get(currency); etf = ETF_HINT.get(currency)
    if yf is None or not pair or not etf: return None
    try:
        t_fx = yf.Ticker(pair).history(period="6mo")["Close"].pct_change().dropna()
        t_etf= yf.Ticker(etf).history(period="6mo")["Close"].pct_change().dropna()
        df = pd.concat([t_fx, t_etf], axis=1).dropna()
        df.columns = ["fx","etf"]
        if df.empty: return None
        # linear regression beta
        b = np.polyfit(df["fx"], df["etf"], 1)[0]
        px_etf = float(yf.Ticker(etf).history(period="1d")["Close"].iloc[-1])
        notional = abs(exposure_usd)*target_pct
        shares = (notional / px_etf) / abs(b) if b!=0 else (notional/px_etf)
        # direction: if exposure benefits from FX up, you short ETF (assuming ETF goes up with FX)
        direction = "SHORT" if exposure_usd>0 else "LONG"
        eff_slip = slippage_bps/10000.0 * notional
        return {"ETF": etf, "Beta": round(b,3), "ETF_Price": round(px_etf,2), "Shares": round(shares,0), "Direction": direction, "Est_Slippage$": round(eff_slip,2)}
    except Exception:
        return None

def page_fx():
    ensure_tabs({
        "FX_Exposure": ["Currency","Exposure_USD","TargetHedgePct","Notes"],
        "FX_Hedges":   ["Timestamp","Currency","Pair","Units","Price","Instrument","Notional_USD","Note"]
    })
    st.subheader("FX & Hedges")
    exp_df = read_df("FX_Exposure!A1:Z1000")
    st.dataframe(exp_df, use_container_width=True, hide_index=True)
    with st.form("fx_add", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns([1,1,1,2])
        cur = c1.selectbox("Currency", list(FX_PAIRS.keys()), index=0)
        exp = c2.number_input("Exposure (USD)", -1e12, 1e12, 0.0, step=100.0)
        tgt = c3.number_input("Target hedge %", 0.0, 100.0, 100.0, 5.0)
        note= c4.text_input("Note")
        if st.form_submit_button("Add/Update exposure"):
            df = read_df("FX_Exposure!A1:Z1000")
            if not df.empty and "Currency" in df.columns and cur in df["Currency"].astype(str).tolist():
                i = df[df["Currency"].astype(str)==cur].index[0] + 2
                write_range(f"FX_Exposure!A{i}:D{i}", [[cur, exp, tgt, note]])
            else:
                append_row("FX_Exposure", [cur, exp, tgt, note])
            st.success("Saved exposure.")
    st.markdown("**ETF Hedge Optimizer**")
    sl = st.number_input("Slippage (bps)", 0.0, 200.0, 5.0, 0.5)
    if st.button("Optimize hedges"):
        outs = []
        for _, r in exp_df.iterrows():
            info = hedge_via_etf(str(r.get("Currency","")), _to_float(r.get("Exposure_USD",0),0.0), _to_float(r.get("TargetHedgePct",100),100)/100.0, slippage_bps=sl)
            if info: outs.append({**{"Currency":r.get("Currency","")}, **info, "Notional_USD": abs(_to_float(r.get("Exposure_USD",0),0.0))*_to_float(r.get("TargetHedgePct",100),100)/100.0})
        if outs:
            st.dataframe(pd.DataFrame(outs), use_container_width=True, hide_index=True)

# ---------- Morning News (unchanged core) ----------
COUNTRY_NEWSAPI = {"US":"us","CA":"ca","MX":"mx","JP":"jp","AU":"au","SG":"sg","IN":"in","GB":"gb","HK":"hk"}
def news_top(country_code: str, q: str=None, page_size=10):
    if not NEWSKEY: return []
    try:
        base = "https://newsapi.org/v2/top-headlines"
        params = {"apiKey": NEWSKEY, "country": country_code, "pageSize": page_size}
        if q: params["q"] = q
        r = requests.get(base, params=params, timeout=6)
        if r.status_code!=200: return []
        articles = r.json().get("articles",[])
        return [{"source":(a.get("source") or {}).get("name",""),"title":a.get("title",""),"url":a.get("url",""),"publishedAt":a.get("publishedAt","")[:19].replace("T"," ")} for a in articles]
    except Exception: return []

def page_news():
    ensure_tabs({"News_Daily": ["Date","Region","Country","Source","Title","URL","Tickers","Notes"],"News_Archive": ["Timestamp","Region","Country","Title","URL"]})
    st.subheader("Morning News"); region = st.radio("Region", ["North America","Asia-Pacific"], index=0, horizontal=True)
    countries = NA_COUNTRIES if region=="North America" else APAC_COUNTRIES
    sel = st.multiselect("Countries", countries, default=countries)
    watch = st.text_input("Tickers (comma-separated)", value="SPY,AAPL,MSFT")
    fetched = []
    if NEWSKEY and st.button("Fetch headlines"):
        for c in sel:
            cc = COUNTRY_NEWSAPI.get(c.upper()); 
            if cc: fetched.extend([{**x, "region":region, "country":c} for x in news_top(cc, page_size=6)])
    if fetched: st.dataframe(pd.DataFrame(fetched), use_container_width=True, hide_index=True)
    if st.button("Append Morning Brief template"):
        today = datetime.utcnow().date().isoformat()
        for c in sel:
            append_row("News_Daily", [today, region, c, "", f"{c} – Key items:", "", watch, ""]) 
        st.success("Template rows appended.")
    with st.form("news_form", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns([1.4,3,3,1.8])
        c  = c1.selectbox("Country", countries, index=0)
        t  = c2.text_input("Title"); u = c3.text_input("URL"); n = c4.text_input("Notes")
        ok = st.form_submit_button("Append item")
        if ok:
            append_row("News_Daily", [datetime.utcnow().date().isoformat(), region, c, "", t, u, watch, n])
            append_row("News_Archive", [now(), region, c, t, u]); st.success("Added.")

# ---------- Health, Docs, Admin ----------
def page_health_min():
    ensure_tabs({"Health_Log":["Timestamp","Mood","SleepHrs","Stress(1-10)","ExerciseMin","Notes"]})
    st.subheader("Wellness Log"); df = read_df("Health_Log!A1:Z2000"); st.dataframe(df, use_container_width=True, hide_index=True)
    with st.form("hlog", clear_on_submit=True):
        c1,c2,c3,c4,c5 = st.columns([1,1,1,1,3])
        mood=c1.selectbox("Mood", ["🙂","😐","🙁","🤩","😴"]); sl=c2.number_input("Sleep",0.0,24.0,7.0,0.5)
        stv=c3.slider("Stress",1,10,4); ex=c4.number_input("Exercise",0,1000,0,5); nt=c5.text_input("Notes")
        if st.form_submit_button("Add"):
            append_row("Health_Log", [now(), mood, sl, stv, ex, nt]); st.success("Logged.")

def export_bundle(tabs: List[str]):
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for t in tabs:
            try:
                df = read_df(f"{t}!A1:Z5000"); z.writestr(f"{t}.csv", df.to_csv(index=False))
            except Exception: pass
    mem.seek(0); return mem

def page_admin_backup():
    st.subheader("Backups & snapshots")
    tabs = st.text_area("Comma-separated tab names to backup", value="NA_Watch,NA_TradeLog,APAC_Watch,APAC_TradeLog,Config")
    if st.button("Snapshot tabs"):
        names = [t.strip() for t in tabs.split(",") if t.strip()]
        created = []
        for t in names:
            try: created.append(snapshot_tab(t))
            except Exception as e: st.error(f"{t}: {e}")
        if created: st.success("Snapshots: " + ", ".join(created))
    if st.button("Download CSV bundle"):
        names = [t.strip() for t in tabs.split(",") if t.strip()]
        z = export_bundle(names); st.download_button("Download bundle.zip", z, file_name="vega_bundle.zip", mime="application/zip")

def page_docs():
    st.subheader("How to use Vega (quick guide)")
    st.markdown("""
**Initial setup**
1) In the sidebar, click **Setup / Repair Google Sheet** once.  
2) On the Watch List (NA/APAC), add rows with `Ticker, Country, Entry, Stop, Target`.
3) Optional config: set `ALERT_PCT`, `RR_TARGET`, `ACCOUNT_EQUITY`, `RISK_PCT` in the **Config** tab.

**Fees / Presets**
- Edit the **Fee_Presets** tab: `Preset, Markets (US,JP,AU,..), Base, BpsBuy, BpsSell, TaxBps`.
- In the close trade box, choose your preset or leave `<auto-match>` to match by `Country` from the Watch List.

**Trading**
- Use **Quick Entry** to log trades. `ExitPrice` + `ExitQty` auto-computes `PnL` and `R` (per unit).  
- Close modes: **Single**, **Average**, **FIFO**, **LIFO**. Fees auto-calc from preset or enter manually.

**Dashboards**
- Inside each cockpit, open **Positions dashboard** for Realized P/L, Open P/L, Win%, Avg R. Filter by **Tags**.

**Earnings**
- Press **Sync earnings** to snapshot upcoming dates to the `Earnings` tab. Tickers with earnings ≤7 days are shown.

**Risk Lab**
- Enter a basket and weights to estimate **1‑day 95% VaR** using 60d covariance.

**Options Builder**
- Pick an expiration and add up to 4 legs (positive=long, negative=short). Computes net Greeks via Black‑Scholes (uses chain IV).

**Broker Import**
- Choose a built‑in profile (IBKR/Tastytrade/Fidelity) or map columns manually. Appends to `NA_TradeLog`/`APAC_TradeLog`.

**FX & Hedges**
- Maintain `FX_Exposure`. Click **Optimize hedges** for ETF suggestions based on historical **beta** vs currency.  
- Log chosen hedges to `FX_Hedges` with one click.

**Backups**
- Use **Admin / Backup** to snapshot tabs or download a CSV bundle.

> Tip: Feature requests go into **V2 Backlog** so we queue up improvements without disrupting trading.
""")

# ---------- Router & Quick Nav ----------
MODULES = ["NA Cockpit","APAC Cockpit","Morning News","Risk Lab","Options Builder","FX & Hedges","Broker Import","Health Journal","Admin / Backup","Docs"]

tabs = st.tabs(MODULES)
with tabs[0]:
    cockpit("North America", "NA_Watch", "NA_TradeLog", NA_COUNTRIES, region_code="NA")
with tabs[1]:
    cockpit("Asia-Pacific", "APAC_Watch", "APAC_TradeLog", APAC_COUNTRIES, region_code="APAC")
with tabs[2]:
    page_news()
with tabs[3]:
    page_risk_lab()
with tabs[4]:
    page_options_builder()
with tabs[5]:
    page_fx()
with tabs[6]:
    page_broker_import()
with tabs[7]:
    page_health_min()
with tabs[8]:
    page_admin_backup()
with tabs[9]:
    page_docs()
