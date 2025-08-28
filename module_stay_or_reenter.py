# -*- coding: utf-8 -*-
from __future__ import annotations

# Streamlit MUST be imported before any st.* calls
import streamlit as st

# Optional PDF lib (graceful fallback if not installed)
try:
    from fpdf import FPDF
except Exception:
    FPDF = None

# Standard libs & 3rd party
import os, io, json, math, time, smtplib, datetime as dt
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import yaml

# ----------------------------
# Constants / Paths
# ----------------------------
DATA_DIR = "data"
CONFIG_DIR = "config"
SECRETS_DIR = "secrets"
LOG_CSV = os.path.join(DATA_DIR, "journal_decisions.csv")
STATE_CSV = os.path.join(DATA_DIR, "decision_state_cache.csv")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "stay_or_reenter.yaml")

# ----------------------------
# Data class
# ----------------------------
@dataclass
class Decision:
    timestamp: str
    ticker: str
    action: str
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
    options_stance: str

# ----------------------------
# Utility functions (stubs)
# ----------------------------
def load_config(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def save_config(cfg: Dict[str, Any], path: str = DEFAULT_CONFIG_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)
    except Exception as e:
        st.warning(f"Could not save config: {e}")

def write_csv_row(path: str, row: Dict[str, Any]) -> None:
    df = pd.DataFrame([row])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)

def log_to_gsheets(row: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    return  # stub

def send_alert(message: str, cfg: Dict[str, Any]) -> None:
    return  # stub

def read_state_cache() -> pd.DataFrame:
    if os.path.exists(STATE_CSV):
        try:
            return pd.read_csv(STATE_CSV)
        except Exception:
            pass
    return pd.DataFrame(columns=["ticker", "last_action"])

def write_state_cache(df: pd.DataFrame) -> None:
    try:
        df.to_csv(STATE_CSV, index=False)
    except Exception:
        pass

# ----------------------------
# Main render function
# ----------------------------
def render_stay_or_reenter():
    st.header("Stay Out vs. Get Back In")
    cfg = load_config()
    # assuming you have _config_pane, _links_bar, etc. defined elsewhere
    cfg = _config_pane(cfg)
    _links_bar(cfg)

    tabs = st.tabs(["Decision", "Re-Entry Tracker"])
    with tabs[0]:
        ticker = st.text_input("Ticker", value="SPY").upper().strip()
        st.caption("Use any tradable symbol supported by yfinance.")

        _relative_strength_panel(ticker, cfg)
        dte = _earnings_block(ticker)
        breadth_mode, breadth_val, risk_on = _breadth_block(cfg)
        exit_count, re_count = _trigger_checklists()
        entry, stop, target, computed_rr, psi = _entry_rr_block(cfg)
        stance = _options_selector_block(ticker, cfg)

        action, why = decide_action(exit_count, re_count, cfg, dte, computed_rr)
        st.subheader("Decision")
        _decision_output(action)
        st.write(why)

        rationale_text = st.text_area(
            "Rationale note (optional)",
            value=("Re-entered on strength breakout" if action == "GET_BACK_IN"
                   else ("Exited for capital efficiency" if action == "STAY_OUT"
                         else "Mixed signals; on watch"))
        )

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
                sector_etf=cfg.get("relative_strength", {}).get("sector_etf", ""),
                rs_benchmark=cfg.get("relative_strength", {}).get("benchmark", "SPY"),
                rs_lookback_days=20,
                rs_vs_benchmark=None,
                rs_vs_sector=None,
                options_stance=stance,
            )
            row = asdict(dec)
            write_csv_row(LOG_CSV, row)
            log_to_gsheets(row, cfg)
            st.success("Logged.")

            state = read_state_cache()
            prev = state[state["ticker"] == ticker]
            last_action = prev.iloc[-1]["last_action"] if not prev.empty else None
            if last_action in ("STAY_OUT", "WAIT") and action == "GET_BACK_IN":
                send_alert(f"{ticker}: flipped to GET BACK IN — {why}", cfg)

            if prev.empty:
                state = pd.concat(
                    [state, pd.DataFrame({"ticker": [ticker], "last_action": [action]})],
                    ignore_index=True
                )
            else:
                state.loc[state["ticker"] == ticker, "last_action"] = action
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
                    sector_etf=cfg.get("relative_strength", {}).get("sector_etf", ""),
                    rs_benchmark=cfg.get("relative_strength", {}).get("benchmark", "SPY"),
                    rs_lookback_days=20,
                    rs_vs_benchmark=None,
                    rs_vs_sector=None,
                    options_stance=stance,
                )
                if FPDF is None:
                    st.warning("PDF export requires the package **fpdf2**. Add `fpdf2>=2.7.9`.")
                else:
                    pdf_bytes = export_pdf(dec, cfg)
                    st.download_button(
                        "Download PDF",
                        data=pdf_bytes,
                        file_name=f"{ticker}_decision.pdf",
                        mime="application/pdf"
                    )
        with cexp2:
            if st.button("Export CSV Row"):
                try:
                    df = pd.read_csv(LOG_CSV)
                    last = df.tail(1)
                    csv = last.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download Last Row",
                        data=csv,
                        file_name="last_decision.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.warning(f"No rows yet: {e}")

        st.markdown("---")
        st.subheader("Watchlist Loop")
        watch_text = st.text_area("Tickers (comma/space separated)", value="SPY, QQQ, IWM")
        if st.button("Scan Watchlist"):
            toks = [t.strip().upper() for t in watch_text.replace("\n", " ").replace(",", " ").split(" ") if t.strip()]
            rows = []
            for tk in toks:
                try:
                    rs_bmk, rs_sec = relative_strength(
                        tk,
                        cfg.get("relative_strength", {}).get("benchmark", "SPY"),
                        cfg.get("relative_strength", {}).get("sector_etf", ""),
                        20
                    )
                    dte_i = next_earnings_days(tk)
                    rows.append({
                        "ticker": tk,
                        "dte": dte_i,
                        "rs_vs_benchmark_pct": None if rs_bmk is None else round(rs_bmk * 100, 2),
                        "rs_vs_sector_pct": None if rs_sec is None else round(rs_sec * 100, 2),
                    })
                except Exception:
                    rows.append({
                        "ticker": tk,
                        "dte": None,
                        "rs_vs_benchmark_pct": None,
                        "rs_vs_sector_pct": None
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tabs[1]:
        _reentry_tracker_tab()
