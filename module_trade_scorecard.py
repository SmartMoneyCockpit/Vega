# -*- coding: utf-8 -*-
"""
AI Trade Quality Scorecard — Vega Trading Cockpit
- Scores each trade 0–100 and grades A–F
- Uses data/trades.csv; optional columns improve scoring:
  rr_planned, r_multiple, followed_plan (bool), stop_respected (bool), setup_quality (1-5),
  earnings_within_30d (bool), risk_off (bool)
"""
from __future__ import annotations
import os, numpy as np, pandas as pd, streamlit as st

DATA_DIR = "data"; TRADES_CSV = os.path.join(DATA_DIR,"trades.csv")
os.makedirs(DATA_DIR, exist_ok=True)

def _load() -> pd.DataFrame:
    if not os.path.exists(TRADES_CSV):
        return pd.DataFrame()
    df = pd.read_csv(TRADES_CSV)
    df.columns = [c.lower() for c in df.columns]
    for c in ["rr_planned","r_multiple","setup_quality"]:
        if c in df.columns: df[c]=pd.to_numeric(df[c], errors="coerce")
    for c in ["followed_plan","stop_respected","earnings_within_30d","risk_off"]:
        if c in df.columns: df[c]=df[c].astype(str).str.lower().isin(["1","true","yes","y"])
        else: df[c]=False
    return df

def _score_row(r: pd.Series) -> tuple[int,str]:
    score = 0
    reasons = []
    # POP: planned RR >= 2 rewarded, >=3 extra
    rr = r.get("rr_planned", np.nan)
    if rr >= 2: score += 15; reasons.append("RR≥2 +15")
    if rr >= 3: score += 10; reasons.append("RR≥3 +10")
    # Realized R multiple
    rm = r.get("r_multiple", np.nan)
    if not np.isnan(rm):
        score += max(min(int(rm*10), 20), -10)  # + up to +20, down to -10
        reasons.append(f"R={rm:.2f} adj")
    # Process discipline
    if r.get("followed_plan", False): score += 15; reasons.append("Followed plan +15")
    if r.get("stop_respected", False): score += 10; reasons.append("Stop respected +10")
    # Setup quality (subjective 1–5)
    sq = r.get("setup_quality", np.nan)
    if not np.isnan(sq): score += int((sq-3)*5)  # -10..+10
    # Risk regime & earnings window penalties
    if r.get("risk_off", False): score -= 5; reasons.append("Risk-off -5")
    if r.get("earnings_within_30d", False): score -= 15; reasons.append("Earnings<30d -15")
    score = int(max(min(score, 100), 0))
    # Grade
    grade = "A" if score>=90 else "B" if score>=80 else "C" if score>=70 else "D" if score>=60 else "F"
    return score, grade + (" ("+", ".join(reasons)+")" if reasons else "")

def render_trade_scorecard():
    st.header("AI Trade Quality Scorecard")
    st.caption("Scores each trade using process + risk rules. Improve input columns for better scoring.")

    df = _load()
    if df.empty:
        st.warning("No trades found (data/trades.csv). Add trades to see scorecard.")
        return

    scores, notes = [], []
    for _, r in df.iterrows():
        s, n = _score_row(r)
        scores.append(s); notes.append(n)
    df["_score"] = scores
    df["_grade"] = ["A" if s>=90 else "B" if s>=80 else "C" if s>=70 else "D" if s>=60 else "F" for s in scores]
    df["_notes"] = notes

    c1,c2,c3 = st.columns(3)
    c1.metric("Avg Score", f"{np.mean(scores):.1f}")
    c2.metric("A/B %", f"{(np.mean([s>=80 for s in scores])*100):.1f}%")
    c3.metric("F %", f"{(np.mean([s<60 for s in scores])*100):.1f}%")

    st.bar_chart(pd.Series(scores, name="Score"), height=200)
    st.dataframe(df[["date","ticker","strategy","rr_planned","r_multiple","_grade","_score","_notes"]], use_container_width=True)
