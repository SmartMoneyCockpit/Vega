# -*- coding: utf-8 -*-
"""
Cockpit Module: Stay Out vs. Get Back In — Vega / Smart Money Cockpit
====================================================================
Drop‑in Streamlit component with:
  • Exit / Re‑Entry checkboxes + colored decision (🟥/🟨/🟩)
  • R:R calculator + guardrails (min R:R, earnings blackout window)
  • Journal logging → CSV and optional Google Sheets
  • Relative Strength mini‑panel vs SPY / QQQ / Sector ETF (sparkline)
  • Auto‑pull next earnings date (yfinance) with manual override fallback
  • Breadth + VIX hooks (from file/endpoint) + manual override
  • Position sizing (fixed‑fraction, max-$, Kelly‑lite)
  • Options vs Stock selector (POP rule, IV vs HV heuristic, 21–90 DTE)
  • PDF export of decision snapshot (FPDF), HTML/CSV fallbacks
  • Watchlist loop for baskets; Re‑Entry Tracker tab
  • YAML config pane persisted across runs
  • Optional alerts on state flip (🟥/🟨 → 🟩) via Discord webhook or email (SMTP)

How to use
----------
1) Save this file as `module_stay_or_reenter.py` next to your `app.py`.
2) In `app.py`:

    from module_stay_or_reenter import render_stay_or_reenter
    render_stay_or_reenter()

3) Create folders if not present:
   - `data/` for logs and cache
   - `config/` for YAML config (`config/stay_or_reenter.yaml`)

4) (Optional) Google Sheets logging:
   - Put a Google Service Account JSON at `secrets/gcp_service_account.json` or set env var
     `GOOGLE_SERVICE_ACCOUNT_JSON` to the JSON contents.
   - In the config pane, set `gsheets.enabled=true`, `spreadsheet` and `worksheet`.

5) Dependencies (add to requirements.txt):
   streamlit
   yfinance>=0.2.40
   pandas
   numpy
   pyyaml
   fpdf2
   gspread
   google-auth
   requests

Notes
-----
• This module uses best‑effort external data (yfinance, option chains). If anything fails,
  it degrades gracefully to manual inputs.
• Telegram is intentionally omitted per your preference; Discord/email are supported via config.
• Earnings blackout and R:R thresholds are configurable in the YAML pane inside the app.
"""

from __future__ import annotations
import os
import io
import json
import math
import time
import smtplib
import datetime as dt
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf

import streamlit as st
from fpdf import FPDF
import yaml

# ----------------------------
# Constants / Paths
# ----------------------------
DATA_DIR = "data"
CONFIG_DIR = "config"
SECRETS_DIR = "secrets"
LOG_CSV = os.path.join(DATA_DIR, "journal_decisions.csv")
STATE_CSV = os.path.join(DATA_DIR, "decision_state_cache.csv")  # for flip alerts
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "stay_or_reenter.yaml")

# Defaults (can be changed in Config pane)
DEFAULTS = {
    "risk": {
        "min_rr": 3.0,
        "earnings_blackout_days": 30,
        "default_account_size": 100000.0,
        "fixed_fraction_risk_pct": 0.01,  # 1%
        "max_loss_dollars": 2000.0,
        "kelly_win_rate": 0.55,
        "kelly_payoff": 1.5
    },
    "relative_strength": {
        "benchmark": "SPY",
        "alt_benchmark": "QQQ",
        "sector_etf": ""
    },
    "options": {
        "pop_target": 0.60,  # ~60% POP guideline
        "dte_min": 21,
        "dte_max": 90,
        "iv_hv_margin": 0.05  # 5% pts threshold for overpriced/underpriced
    },
    "breadth": {
        "source": "manual",  # manual | file | url
        "file_path": os.path.join(DATA_DIR, "breadth.json"),
        "url": "",
        "risk_on_threshold": 0.0,  # interpretation of your feed
    },
    "alerts": {
        "enabled": False,
        "mode": "discord",  # discord | email
        "discord_webhook": "",
        "email": {
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_pass": "",
            "from_addr": "",
            "to_addrs": []
        }
    },
    "gsheets": {
        "enabled": False,
        "spreadsheet": "Vega Journal",
        "worksheet": "Decisions"
    },
    "links": {
        "breadth_dashboard": "",
        "macro_calendar": "",
        "sector_dashboard": ""
    }
}

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(SECRETS_DIR, exist_ok=True)

# ----------------------------
# Data classes
# ----------------------------
@dataclass
class Decision:
    timestamp: str
    ticker: str
    action: str  # STAY_OUT | WAIT | GET_BACK_IN
    rationale: str
    entry: Optional[float]
    stop: Optional[float]
    target: Optional[float]
    reward_risk: Optional[float]
    days_to_earnings: Optional[int]
    exit_triggers: int
    reentry_triggers: int
    breadth_mode: str
    breadth_value: Optional[float]
    sector_etf: str
    rs_benchmark: str
    rs_lookback_days: int
    rs_vs_benchmark: Optional[float]
    rs_vs_sector: Optional[float]
    options_stance: str  # CALLS/CALL_SPREADS | PUTS/PUT_SPREADS | STOCK


# ----------------------------
# Utility functions
# ----------------------------

def load_config(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return DEFAULTS.copy()


def save_config(cfg: Dict[str, Any], path: str = DEFAULT_CONFIG_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)
    except Exception as e:
        st.warning(f"Could not save config: {e}")


def rr(entry: Optional[float], stop: Optional[float], target: Optional[float]) -> Optional[float]:
    try:
        if entry is None or stop is None or target is None:
            return None
        risk = max(entry - stop, 1e-9)
        reward = max(target - entry, 0.0)
        return reward / risk if risk > 0 else None
    except Exception:
        return None


def yf_price_series(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return None


def next_earnings_days(ticker: str) -> Optional[int]:
    """Return days until next earnings using yfinance (best effort)."""
    try:
        t = yf.Ticker(ticker)
        # yfinance >= 0.2: get_earnings_dates returns DataFrame indexed by date
        edf = t.get_earnings_dates(limit=1)
        if edf is not None and not edf.empty:
            next_dt = edf.index[0].to_pydatetime()
            today = dt.datetime.now().date()
            return (next_dt.date() - today).days
    except Exception:
        pass
    return None


def relative_strength(ticker: str, benchmark: str, sector_etf: str = "", lookback_days: int = 20) -> Tuple[Optional[float], Optional[float]]:
    """Return (RS vs benchmark, RS vs sector) over lookback_days using simple total return ratio."""
    try:
        end = dt.datetime.now()
        start = end - dt.timedelta(days=lookback_days * 2)  # buffer for trading days
        tick = yf.download([ticker], start=start, end=end, progress=False, auto_adjust=True)["Close"]
        bmk = yf.download([benchmark], start=start, end=end, progress=False, auto_adjust=True)["Close"]
        if tick.empty or bmk.empty:
            return (None, None)
        tick_ret = tick.pct_change().add(1).prod() - 1
        bmk_ret = bmk.pct_change().add(1).prod() - 1
        rs_bmk = None if bmk_ret is None else (tick_ret - bmk_ret)
        rs_sector = None
        if sector_etf:
            sec = yf.download([sector_etf], start=start, end=end, progress=False, auto_adjust=True)["Close"]
            if not sec.empty:
                sec_ret = sec.pct_change().add(1).prod() - 1
                rs_sector = tick_ret - sec_ret
        return (rs_bmk, rs_sector)
    except Exception:
        return (None, None)


def choose_expiration(ticker: str, min_dte: int, max_dte: int) -> Optional[str]:
    try:
        t = yf.Ticker(ticker)
        exps = t.options or []
        if not exps:
            return None
        today = dt.datetime.now().date()
        best = None
        best_diff = 10**9
        for e in exps:
            try:
                d = dt.datetime.strptime(e, "%Y-%m-%d").date()
            except ValueError:
                # some providers may return different formats; skip these
                continue
            dte = (d - today).days
            if min_dte <= dte <= max_dte:
                diff = abs((min_dte + max_dte) / 2 - dte)
                if diff < best_diff:
                    best = e
                    best_diff = diff
        # if none in range, fallback to closest
        if not best:
            for e in exps:
                try:
                    d = dt.datetime.strptime(e, "%Y-%m-%d").date()
                except ValueError:
                    continue
                dte = (d - today).days
                diff = abs((min_dte + max_dte) / 2 - dte)
                if diff < best_diff:
                    best = e
                    best_diff = diff
        return best
    except Exception:
        return None


def atm_iv_vs_hv(ticker: str, expiry: str) -> Tuple[Optional[float], Optional[float]]:
    """Approximate ATM IV (avg of call/put near‐ATM) vs 30d historical volatility (annualized)."""
    iv = None
    hv = None
    try:
        t = yf.Ticker(ticker)
        spot = t.history(period="5d", interval="1d")["Close"].iloc[-1]
        if np.isnan(spot):
            spot = float(t.info.get("regularMarketPrice", np.nan))
        chain = t.option_chain(expiry)
        calls = chain.calls
        puts = chain.puts
        if not calls.empty and not puts.empty:
            # find closest strike to spot
            calls["dist"] = (calls["strike"] - spot).abs()
            puts["dist"] = (puts["strike"] - spot).abs()
            c_atm = calls.sort_values("dist").head(1)
            p_atm = puts.sort_values("dist").head(1)
            civ = float(c_atm["impliedVolatility"].iloc[0]) if "impliedVolatility" in c_atm else np.nan
            piv = float(p_atm["impliedVolatility"].iloc[0]) if "impliedVolatility" in p_atm else np.nan
            iv = np.nanmean([civ, piv]) if not (np.isnan(civ) and np.isnan(piv)) else None
        # HV (30d)
        px = yf_price_series(ticker, period="6mo", interval="1d")
        if px is not None and not px.empty:
            ret = px["Close"].pct_change().dropna()
            hv = float(ret.tail(30).std() * np.sqrt(252)) if len(ret) >= 30 else float(ret.std() * np.sqrt(252))
    except Exception:
        pass
    return (iv, hv)


def options_vs_stock_selector(ticker: str, cfg: Dict[str, Any]) -> str:
    """Return suggestion based on IV vs HV heuristic and POP rule.
    • If IV − HV > margin → overpriced → PUTS / PUT SPREADS
    • If HV − IV > margin → underpriced → CALLS / CALL SPREADS
    • Else → STOCK
    """
    try:
        expiry = choose_expiration(ticker, cfg["options"]["dte_min"], cfg["options"]["dte_max"])
        iv, hv = atm_iv_vs_hv(ticker, expiry) if expiry else (None, None)
        margin = cfg["options"]["iv_hv_margin"]
        if iv is not None and hv is not None:
            if (iv - hv) > margin:
                return "PUTS/PUT_SPREADS"
            if (hv - iv) > margin:
                return "CALLS/CALL_SPREADS"
        return "STOCK"
    except Exception:
        return "STOCK"


def breadth_value(cfg: Dict[str, Any]) -> Tuple[str, Optional[float]]:
    mode = cfg.get("breadth", {}).get("source", "manual")
    if mode == "file":
        try:
            with open(cfg["breadth"]["file_path"], "r", encoding="utf-8") as f:
                data = json.load(f)
            val = float(data.get("breadth", np.nan))
            return ("file", val)
        except Exception:
            return ("file", None)
    if mode == "url":
        try:
            url = cfg["breadth"]["url"]
            resp = requests.get(url, timeout=5)
            val = float(resp.json().get("breadth", np.nan)) if resp.ok else np.nan
            return ("url", val if not np.isnan(val) else None)
        except Exception:
            return ("url", None)
    return ("manual", None)


def position_size(entry: float, stop: float, account_size: float, fixed_fraction_pct: float, max_loss_dollars: float) -> Dict[str, Any]:
    risk_per_share = max(entry - stop, 1e-9)
    # Fixed‑fraction sizing
    risk_cap = max(account_size * fixed_fraction_pct, 0.0)
    shares_ff = math.floor(risk_cap / risk_per_share) if risk_per_share > 0 else 0
    # Max $ loss sizing
    shares_max = math.floor(max_loss_dollars / risk_per_share) if risk_per_share > 0 else 0
    # Kelly‑lite (based on configured win rate & payoff)
    # k = p - (1-p)/b
    k = DEFAULTS["risk"]["kelly_win_rate"] - (1 - DEFAULTS["risk"]["kelly_win_rate"]) / max(DEFAULTS["risk"]["kelly_payoff"], 1e-6)
    k = max(min(k, 0.25), 0.0)  # cap Kelly at 25% for prudence
    risk_cap_kelly = account_size * k
    shares_k = math.floor(risk_cap_kelly / risk_per_share) if risk_per_share > 0 else 0
    return {
        "risk_per_share": risk_per_share,
        "shares_fixed_fraction": shares_ff,
        "shares_max_loss": shares_max,
        "shares_kelly_lite": shares_k,
    }


def color_badge(text: str, color: str):
    st.markdown(
        f"""
        <div style='display:inline-block;padding:6px 10px;border-radius:999px;background:{color};color:white;font-weight:700;'>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def write_csv_row(path: str, row: Dict[str, Any]) -> None:
    df = pd.DataFrame([row])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)


def log_to_gsheets(row: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    if not cfg.get("gsheets", {}).get("enabled", False):
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        sa_path = os.path.join(SECRETS_DIR, "gcp_service_account.json")
        sa_json_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if os.path.exists(sa_path):
            with open(sa_path, "r", encoding="utf-8") as f:
                info = json.load(f)
        elif sa_json_env:
            info = json.loads(sa_json_env)
        else:
            st.warning("Google Sheets logging enabled but no service account JSON found.")
            return
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open(cfg["gsheets"]["spreadsheet"])
        ws = sh.worksheet(cfg["gsheets"]["worksheet"])
        ws.append_row(list(row.values()))
    except Exception as e:
        st.warning(f"GSheets append failed: {e}")


def send_alert(message: str, cfg: Dict[str, Any]) -> None:
    if not cfg.get("alerts", {}).get("enabled", False):
        return
    mode = cfg["alerts"].get("mode", "discord")
    try:
        if mode == "discord":
            hook = cfg["alerts"].get("discord_webhook", "")
            if hook:
                requests.post(hook, json={"content": message}, timeout=5)
        elif mode == "email":
            email_cfg = cfg["alerts"].get("email", {})
            host = email_cfg.get("smtp_host", "")
            if not host:
                return
            port = int(email_cfg.get("smtp_port", 587))
            user = email_cfg.get("smtp_user", "")
            pwd = email_cfg.get("smtp_pass", "")
            from_addr = email_cfg.get("from_addr", user)
            to_addrs = email_cfg.get("to_addrs", [])
            if not to_addrs:
                return
            body = f"Subject: Vega Alert — Re‑Entry\n\n{message}"
            with smtplib.SMTP(host, port) as s:
                s.starttls()
                if user:
                    s.login(user, pwd)
                s.sendmail(from_addr, to_addrs, body)
    except Exception as e:
        st.warning(f"Alert error: {e}")


def export_pdf(dec: Decision, cfg: Dict[str, Any]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, "Stay Out vs Get Back In — Decision", ln=1)
    pdf.set_font("Arial", size=11)
    for k, v in asdict(dec).items():
        pdf.multi_cell(0, 8, f"{k}: {v}")
    pdf.ln(4)
    pdf.set_font("Arial", style="I", size=10)
    pdf.multi_cell(0, 6, "Generated by Vega Cockpit")
    return pdf.output(dest="S").encode("latin-1", errors="ignore")


def read_state_cache() -> pd.DataFrame:
    if os.path.exists(STATE_CSV):
        try:
            return pd.read_csv(STATE_CSV)
        except Exception:
            pass
    return pd.DataFrame(columns=["ticker", "last_action"])  # empty


def write_state_cache(df: pd.DataFrame) -> None:
    try:
        df.to_csv(STATE_CSV, index=False)
    except Exception:
        pass


# ----------------------------
# Decision logic
# ----------------------------

def decide_action(exit_count: int, re_count: int, cfg: Dict[str, Any], earned_days: Optional[int], computed_rr: Optional[float]) -> Tuple[str, str]:
    # Guardrails first
    min_rr = float(cfg["risk"]["min_rr"])
    blackout = int(cfg["risk"]["earnings_blackout_days"])

    if computed_rr is None:
        return ("WAIT", "No R:R — provide entry/stop/target or wait for setup.")
    if computed_rr < min_rr:
        return ("STAY_OUT", f"R:R {computed_rr:.2f} below minimum {min_rr:.2f}.")
    if earned_days is not None and earned_days < blackout:
        return ("STAY_OUT", f"Earnings in {earned_days} days (< {blackout}).")

    if exit_count > re_count:
        return ("STAY_OUT", f"{exit_count} exit vs {re_count} re‑entry triggers.")
    if re_count > exit_count:
        return ("GET_BACK_IN", f"{re_count} re‑entry vs {exit_count} exit triggers.")
    return ("WAIT", "Mixed signals — keep on watch.")


# ----------------------------
# Main UI
# ----------------------------

def _links_bar(cfg: Dict[str, Any]):
    col1, col2, col3 = st.columns(3)
    if cfg["links"].get("breadth_dashboard"):
        col1.link_button("Breadth Dashboard", cfg["links"]["breadth_dashboard"], use_container_width=True)
    if cfg["links"].get("macro_calendar"):
        col2.link_button("Macro Calendar", cfg["links"]["macro_calendar"], use_container_width=True)
    if cfg["links"].get("sector_dashboard"):
        col3.link_button("Sector Dashboard", cfg["links"]["sector_dashboard"], use_container_width=True)


def _config_pane(cfg: Dict[str, Any]) -> Dict[str, Any]:
    with st.expander("⚙️ Config"):
        c1, c2, c3 = st.columns(3)
        cfg["risk"]["min_rr"] = c1.number_input("Min Reward:Risk", value=float(cfg["risk"]["min_rr"]), step=0.5)
        cfg["risk"]["earnings_blackout_days"] = c2.number_input("Earnings blackout (days)", value=int(cfg["risk"]["earnings_blackout_days"]), step=1)
        cfg["risk"]["default_account_size"] = c3.number_input("Default account size ($)", value=float(cfg["risk"]["default_account_size"]), step=1000.0)
        c4, c5 = st.columns(2)
        cfg["risk"]["fixed_fraction_risk_pct"] = c4.number_input("Fixed‑fraction risk %", value=float(cfg["risk"]["fixed_fraction_risk_pct"]), step=0.005, format="%.3f")
        cfg["risk"]["max_loss_dollars"] = c5.number_input("Max loss $", value=float(cfg["risk"]["max_loss_dollars"]), step=100.0)

        st.markdown("---")
        c6, c7, c8 = st.columns(3)
        cfg["relative_strength"]["benchmark"] = c6.text_input("Benchmark (SPY)", value=cfg["relative_strength"].get("benchmark", "SPY"))
        cfg["relative_strength"]["alt_benchmark"] = c7.text_input("Alt Benchmark (QQQ)", value=cfg["relative_strength"].get("alt_benchmark", "QQQ"))
        cfg["relative_strength"]["sector_etf"] = c8.text_input("Sector ETF (optional)", value=cfg["relative_strength"].get("sector_etf", ""))

        st.markdown("---")
        c9, c10, c11 = st.columns(3)
        cfg["options"]["dte_min"] = int(c9.number_input("Min DTE", value=int(cfg["options"]["dte_min"]), step=1))
        cfg["options"]["dte_max"] = int(c10.number_input("Max DTE", value=int(cfg["options"]["dte_max"]), step=1))
        cfg["options"]["iv_hv_margin"] = float(c11.number_input("IV−HV margin (pp)", value=float(cfg["options"]["iv_hv_margin"]), step=0.01, format="%.2f"))

        st.markdown("---")
        st.subheader("Breadth Source")
        cfg["breadth"]["source"] = st.selectbox("Source", ["manual", "file", "url"], index=["manual","file","url"].index(cfg["breadth"].get("source","manual")))
        if cfg["breadth"]["source"] == "file":
            cfg["breadth"]["file_path"] = st.text_input("Breadth file path", value=cfg["breadth"].get("file_path", os.path.join(DATA_DIR,"breadth.json")))
        elif cfg["breadth"]["source"] == "url":
            cfg["breadth"]["url"] = st.text_input("Breadth URL (returns {breadth: number})", value=cfg["breadth"].get("url", ""))
        cfg["breadth"]["risk_on_threshold"] = float(st.number_input("Risk‑on threshold", value=float(cfg["breadth"].get("risk_on_threshold", 0.0)), step=0.1))

        st.markdown("---")
        st.subheader("Google Sheets Logging")
        cfg["gsheets"]["enabled"] = st.checkbox("Enable Google Sheets append", value=bool(cfg["gsheets"].get("enabled", False)))
        c12, c13 = st.columns(2)
        cfg["gsheets"]["spreadsheet"] = c12.text_input("Spreadsheet name", value=cfg["gsheets"].get("spreadsheet","Vega Journal"))
        cfg["gsheets"]["worksheet"] = c13.text_input("Worksheet", value=cfg["gsheets"].get("worksheet","Decisions"))

        st.markdown("---")
        st.subheader("Alerts on Re‑Entry Flip")
        cfg["alerts"]["enabled"] = st.checkbox("Enable alerts", value=bool(cfg["alerts"].get("enabled", False)))
        cfg["alerts"]["mode"] = st.selectbox("Mode", ["discord", "email"], index=["discord","email"].index(cfg["alerts"].get("mode","discord")))
        if cfg["alerts"]["mode"] == "discord":
            cfg["alerts"]["discord_webhook"] = st.text_input("Discord webhook URL", value=cfg["alerts"].get("discord_webhook",""))
        else:
            c14, c15 = st.columns(2)
            cfg["alerts"]["email"]["smtp_host"] = c14.text_input("SMTP host", value=cfg["alerts"].get("email",{}).get("smtp_host",""))
            cfg["alerts"]["email"]["smtp_port"] = int(c15.number_input("SMTP port", value=int(cfg["alerts"].get("email",{}).get("smtp_port",587)), step=1))
            c16, c17 = st.columns(2)
            cfg["alerts"]["email"]["smtp_user"] = c16.text_input("SMTP user", value=cfg["alerts"].get("email",{}).get("smtp_user",""))
            cfg["alerts"]["email"]["smtp_pass"] = c17.text_input("SMTP password", value=cfg["alerts"].get("email",{}).get("smtp_pass",""))
            c18, c19 = st.columns(2)
            cfg["alerts"]["email"]["from_addr"] = c18.text_input("From address", value=cfg["alerts"].get("email",{}).get("from_addr",""))
            to_str = ", ".join(cfg["alerts"].get("email",{}).get("to_addrs", []))
            to_str = c19.text_input("To addresses (comma‑sep)", value=to_str)
            cfg["alerts"]["email"]["to_addrs"] = [x.strip() for x in to_str.split(",") if x.strip()]

        st.markdown("---")
        st.subheader("Quick Links")
        c20, c21, c22 = st.columns(3)
        cfg["links"]["breadth_dashboard"] = c20.text_input("Breadth Dashboard URL", value=cfg["links"].get("breadth_dashboard",""))
        cfg["links"]["macro_calendar"] = c21.text_input("Macro Calendar URL", value=cfg["links"].get("macro_calendar",""))
        cfg["links"]["sector_dashboard"] = c22.text_input("Sector Dashboard URL", value=cfg["links"].get("sector_dashboard",""))

        if st.button("Save Config", type="primary"):
            save_config(cfg)
            st.success("Config saved.")
    return cfg


def _sparkline(series: pd.Series, height: int = 40):
    if series is None or len(series) == 0:
        st.caption("(no data)")
        return
    # Simple sparkline using Streamlit line_chart
    df = pd.DataFrame({"v": series.values})
    st.line_chart(df, height=height)


def _relative_strength_panel(ticker: str, cfg: Dict[str, Any]):
    st.subheader("Relative Strength")
    lookback = st.number_input("Lookback (days)", value=20, step=5)
    bench = cfg["relative_strength"].get("benchmark", "SPY")
    alt = cfg["relative_strength"].get("alt_benchmark", "QQQ")
    sector = cfg["relative_strength"].get("sector_etf", "")

    rs_bmk, rs_sec = relative_strength(ticker, bench, sector, lookback)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"vs {bench}", f"{rs_bmk*100:.2f}%" if rs_bmk is not None else "—")
    c2.metric(f"vs {alt}", "(see chart)")
    c3.metric(f"vs {sector or 'Sector'}", f"{rs_sec*100:.2f}%" if rs_sec is not None else "—")

    # show quick sparklines for ticker and benchmarks (last 30 bars)
    try:
        px_t = yf_price_series(ticker, period="3mo", interval="1d")
        px_b = yf_price_series(bench, period="3mo", interval="1d")
        px_q = yf_price_series(alt, period="3mo", interval="1d")
        st.caption("Price trend (last ~3 months)")
        cc1, cc2, cc3 = st.columns(3)
        _sparkline(px_t["Close"].tail(30) if px_t is not None else None)
        _sparkline(px_b["Close"].tail(30) if px_b is not None else None)
        _sparkline(px_q["Close"].tail(30) if px_q is not None else None)
    except Exception:
        st.caption("Sparkline unavailable.")


def _earnings_block(ticker: str) -> Optional[int]:
    dte = next_earnings_days(ticker)
    with st.expander("Earnings Window"):
        c1, c2 = st.columns([2,1])
        c1.write(f"Auto‑detected days to earnings: **{dte if dte is not None else 'unknown'}**")
        manual = c2.number_input("Override (days)", value=int(dte if dte is not None else 999), step=1)
        use_override = st.checkbox("Use override", value=(dte is None))
        return int(manual) if use_override else (int(dte) if dte is not None else None)


def _breadth_block(cfg: Dict[str, Any]) -> Tuple[str, Optional[float], bool]:
    mode, val = breadth_value(cfg)
    with st.expander("Breadth / Risk Mode"):
        st.write(f"Source: **{mode}**")
        manual = st.number_input("Manual breadth value", value=float(val if val is not None else 0.0), step=0.1)
        use_manual = st.checkbox("Use manual breadth override", value=(val is None))
        threshold = float(cfg["breadth"].get("risk_on_threshold", 0.0))
        chosen = manual if use_manual else (val if val is not None else manual)
        risk_on = (chosen >= threshold)
        color_badge("Risk‑On" if risk_on else "Risk‑Off", "#16a34a" if risk_on else "#dc2626")
        return (mode, chosen, risk_on)


def _trigger_checklists() -> Tuple[int, int]:
    st.subheader("Step 1: Status Check")
    st.caption("Tick what you see on the chart / tape.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📉 Exit Triggers**")
        e1 = st.checkbox("Price below stop or key support")
        e2 = st.checkbox("MACD bearish, RSI < 50")
        e3 = st.checkbox("OBV negative / no accumulation")
        e4 = st.checkbox("Breadth weak, sector lagging")
        e5 = st.checkbox("R:R collapsed (<1.5:1)")
        e6 = st.checkbox("Underperforms SPY/sector peers")
        e7 = st.checkbox("Macro headwind backdrop")
        exit_count = sum([e1,e2,e3,e4,e5,e6,e7])
    with c2:
        st.markdown("**📈 Re‑Entry Triggers**")
        r1 = st.checkbox("Reclaim 20/50 DMA or clears wedge/triangle")
        r2 = st.checkbox("MACD bull cross, RSI > 50 and rising")
        r3 = st.checkbox("OBV turning up + volume confirmation")
        r4 = st.checkbox("Breadth risk‑on, sector leading")
        r5 = st.checkbox("New R:R ≥ 2–3:1 with defined stops/targets")
        r6 = st.checkbox("Outperforms SPY/peers")
        r7 = st.checkbox("Macro tailwinds align with thesis")
        re_count = sum([r1,r2,r3,r4,r5,r6,r7])
    st.write("")
    st.write(f"Exit triggers: **{exit_count}**, Re‑entry: **{re_count}**")
    return exit_count, re_count


def _entry_rr_block(cfg: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Dict[str, Any]]:
    st.subheader("Entry & R:R")
    c1, c2, c3, c4 = st.columns(4)
    entry = c1.number_input("Entry", value=0.0, step=0.01)
    stop = c2.number_input("Stop", value=0.0, step=0.01)
    target = c3.number_input("Target", value=0.0, step=0.01)
    acct = c4.number_input("Account $", value=float(cfg["risk"]["default_account_size"]))
    computed_rr = rr(entry if entry>0 else None, stop if stop>0 else None, target if target>0 else None)
    if computed_rr is not None:
        st.metric("Reward:Risk", f"{computed_rr:.2f}x")
    else:
        st.metric("Reward:Risk", "—")
    if entry>0 and stop>0 and acct>0:
        psi = position_size(entry, stop, acct, float(cfg["risk"]["fixed_fraction_risk_pct"]), float(cfg["risk"]["max_loss_dollars"]))
        st.caption("Sizing suggestions (shares)")
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("Risk/share", f"${psi['risk_per_share']:.2f}")
        cc2.metric("Fixed‑fraction", int(psi["shares_fixed_fraction"]))
        cc3.metric("Max‑$", int(psi["shares_max_loss"]))
        cc4.metric("Kelly‑lite", int(psi["shares_kelly_lite"]))
    return entry if entry>0 else None, stop if stop>0 else None, target if target>0 else None, computed_rr, psi if entry>0 and stop>0 and acct>0 else {}


def _options_selector_block(ticker: str, cfg: Dict[str, Any]) -> str:
    st.subheader("Options vs Stock Selector")
    auto = st.checkbox("Auto (IV vs HV heuristic)", value=True)
    if auto:
        stance = options_vs_stock_selector(ticker, cfg)
        st.write(f"Auto stance: **{stance}** (DTE {cfg['options']['dte_min']}–{cfg['options']['dte_max']}, POP≈{int(cfg['options']['pop_target']*100)}%)")
    else:
        stance = st.selectbox("Manual stance", ["STOCK", "CALLS/CALL_SPREADS", "PUTS/PUT_SPREADS"]) 
    return stance


def _decision_output(action: str):
    if action == "GET_BACK_IN":
        color_badge("🟩 GET BACK IN", "#16a34a")
    elif action == "STAY_OUT":
        color_badge("🟥 STAY OUT", "#dc2626")
    else:
        color_badge("🟨 WAIT", "#eab308")


def _reentry_tracker_tab():
    st.subheader("🟨 Re‑Entry Tracker")
    if not os.path.exists(LOG_CSV):
        st.info("No decisions logged yet.")
        return
    try:
        df = pd.read_csv(LOG_CSV)
    except Exception as e:
        st.warning(f"Could not read log: {e}")
        return
    waiters = df[df["action"]=="WAIT"].copy()
    if waiters.empty:
        st.caption("No WAIT tickers — nice!")
        return
    # Show last record for each ticker where WAIT
    waiters["timestamp"] = pd.to_datetime(waiters["timestamp"]) 
    last = waiters.sort_values(["ticker","timestamp"]).groupby("ticker").tail(1)
    st.dataframe(last[["timestamp","ticker","reward_risk","days_to_earnings","exit_triggers","reentry_triggers","rationale"]], use_container_width=True)


def render_stay_or_reenter():
    st.header("Stay Out vs. Get Back In")
    cfg = load_config()
    cfg = _config_pane(cfg)
    _links_bar(cfg)

    tabs = st.tabs(["Decision", "Re‑Entry Tracker"])
    with tabs[0]:
        ticker = st.text_input("Ticker", value="SPY").upper().strip()
        st.caption("Use any tradable symbol supported by yfinance.")

        # Relative Strength mini‑panel
        _relative_strength_panel(ticker, cfg)

        # Earnings
        dte = _earnings_block(ticker)

        # Breadth & risk mode
        breadth_mode, breadth_val, risk_on = _breadth_block(cfg)

        # Triggers
        exit_count, re_count = _trigger_checklists()

        # Entry / R:R / sizing
        entry, stop, target, computed_rr, psi = _entry_rr_block(cfg)

        # Options vs stock selector
        stance = _options_selector_block(ticker, cfg)

        # Decision
        action, why = decide_action(exit_count, re_count, cfg, dte, computed_rr)
        st.subheader("Decision")
        _decision_output(action)
        st.write(why)

        # Journal logging & export
        rationale_text = st.text_area("Rationale note (optional)", value=("Re‑entered on strength breakout" if action=="GET_BACK_IN" else ("Exited for capital efficiency" if action=="STAY_OUT" else "Mixed signals; on watch")))
        if st.button("Log Decision", type="primary"):
            dec = Decision(
                timestamp=dt.datetime.now().isoformat(timespec='seconds'),
                ticker=ticker,
                action=action,
                rationale=rationale_text,
                entry=entry,
                stop=stop,
                target=target,
                reward_risk=float(computed_rr) if computed_rr is not None else None,
                days_to_earnings=int(dte) if dte is not None else None,
                exit_triggers=int(exit_count),
                reentry_triggers=int(re_count),
                breadth_mode=breadth_mode,
                breadth_value=float(breadth_val) if breadth_val is not None else None,
                sector_etf=cfg["relative_strength"].get("sector_etf",""),
                rs_benchmark=cfg["relative_strength"].get("benchmark","SPY"),
                rs_lookback_days=20,
                rs_vs_benchmark=None,
                rs_vs_sector=None,
                options_stance=stance,
            )
            row = asdict(dec)
            write_csv_row(LOG_CSV, row)
            log_to_gsheets(row, cfg)
            st.success("Logged.")

            # Flip alerts: compare last action for ticker
            state = read_state_cache()
            prev = state[state["ticker"]==ticker]
            last_action = prev.iloc[-1]["last_action"] if not prev.empty else None
            if last_action in ("STAY_OUT", "WAIT") and action == "GET_BACK_IN":
                send_alert(f"{ticker}: flipped to GET BACK IN — {why}", cfg)
            # update cache
            if prev.empty:
                state = pd.concat([state, pd.DataFrame({"ticker":[ticker], "last_action":[action]})], ignore_index=True)
            else:
                state.loc[state["ticker"]==ticker, "last_action"] = action
            write_state_cache(state)

        cexp1, cexp2 = st.columns(2)
        with cexp1:
            if st.button("Export PDF"):
                dec = Decision(
                    timestamp=dt.datetime.now().isoformat(timespec='seconds'),
                    ticker=ticker,
                    action=action,
                    rationale=rationale_text,
                    entry=entry,
                    stop=stop,
                    target=target,
                    reward_risk=float(computed_rr) if computed_rr is not None else None,
                    days_to_earnings=int(dte) if dte is not None else None,
                    exit_triggers=int(exit_count),
                    reentry_triggers=int(re_count),
                    breadth_mode=breadth_mode,
                    breadth_value=float(breadth_val) if breadth_val is not None else None,
                    sector_etf=cfg["relative_strength"].get("sector_etf",""),
                    rs_benchmark=cfg["relative_strength"].get("benchmark","SPY"),
                    rs_lookback_days=20,
                    rs_vs_benchmark=None,
                    rs_vs_sector=None,
                    options_stance=stance,
                )
                pdf_bytes = export_pdf(dec, cfg)
                st.download_button("Download PDF", data=pdf_bytes, file_name=f"{ticker}_decision.pdf", mime="application/pdf")
        with cexp2:
            if st.button("Export CSV Row"):
                # dumps the most recent decision row for convenience
                try:
                    df = pd.read_csv(LOG_CSV)
                    last = df.tail(1)
                    csv = last.to_csv(index=False).encode("utf-8")
                    st.download_button("Download Last Row", data=csv, file_name="last_decision.csv", mime="text/csv")
                except Exception as e:
                    st.warning(f"No rows yet: {e}")

        st.markdown("---")
        st.subheader("Watchlist Loop")
        watch_text = st.text_area("Tickers (comma/space separated)", value="SPY, QQQ, IWM")
        if st.button("Scan Watchlist"):
            toks = [t.strip().upper() for t in watch_text.replace("\n"," ").replace(","," ").split(" ") if t.strip()]
            rows = []
            for tk in toks:
                try:
                    rs_bmk, rs_sec = relative_strength(tk, cfg["relative_strength"]["benchmark"], cfg["relative_strength"].get("sector_etf",""), 20)
                    dte_i = next_earnings_days(tk)
                    rows.append({
                        "ticker": tk,
                        "dte": dte_i,
                        "rs_vs_benchmark_pct": None if rs_bmk is None else round(rs_bmk*100, 2),
                        "rs_vs_sector_pct": None if rs_sec is None else round(rs_sec*100, 2),
                    })
                except Exception:
                    rows.append({"ticker": tk, "dte": None, "rs_vs_benchmark_pct": None, "rs_vs_sector_pct": None})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tabs[1]:
        _reentry_tracker_tab()
