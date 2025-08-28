# -*- coding: utf-8 -*-
"""
Auto-Journal Generator — Vega Trading Cockpit
- Builds a daily text journal from decisions & trades
- Sources:
  - Decisions: data/journal_decisions.csv  (from stay_or_reenter)
  - Trades:    data/trades.csv
- Output:     data/journal/YYYY-MM-DD.md (download + save)
- Optional: Email the summary using the same SMTP fields (email only)
"""
from __future__ import annotations
import os, io, datetime as dt, pandas as pd, numpy as np, streamlit as st, yaml, ssl, smtplib

DATA_DIR = "data"; CONFIG_DIR = "config"
DECISIONS_CSV = os.path.join(DATA_DIR, "journal_decisions.csv")
TRADES_CSV    = os.path.join(DATA_DIR, "trades.csv")
JOURNAL_DIR   = os.path.join(DATA_DIR, "journal")
CFG_PATH      = os.path.join(CONFIG_DIR, "stay_or_reenter.yaml")
os.makedirs(JOURNAL_DIR, exist_ok=True)

def _load_cfg() -> dict:
    if os.path.exists(CFG_PATH):
        try:
            return yaml.safe_load(open(CFG_PATH,"r",encoding="utf-8")) or {}
        except Exception:
            pass
    return {}

def _email_cfg(cfg: dict) -> dict:
    return (cfg.get("alerts",{}) or {}).get("email", {})

def _safe_send_email(subject: str, body: str, cfg_email: dict) -> tuple[bool,str]:
    host = cfg_email.get("smtp_host",""); port = int(cfg_email.get("smtp_port",587))
    user = cfg_email.get("smtp_user","");  pwd  = cfg_email.get("smtp_pass","")
    from_addr = cfg_email.get("from_addr", user or "no-reply@vega")
    to_addrs  = cfg_email.get("to_addrs", [])
    if not host or not to_addrs: return False, "Missing SMTP host or to_addrs"
    msg = f"Subject: {subject}\r\nFrom: {from_addr}\r\nTo: {', '.join(to_addrs)}\r\n\r\n{body}"
    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls(context=ssl.create_default_context())
            if user: s.login(user, pwd)
            s.sendmail(from_addr, to_addrs, msg)
        return True, "sent"
    except Exception as e:
        return False, str(e)

def _load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path): return pd.DataFrame()
    try: return pd.read_csv(path)
    except: return pd.DataFrame()

def _mk_summary(day: dt.date, trades: pd.DataFrame, decisions: pd.DataFrame) -> str:
    dstr = day.isoformat()
    t = trades.copy()
    d = decisions.copy()
    for df in (t,d):
        if "date" in df.columns: df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        if "timestamp" in df.columns: df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    tday = t[t.get("date",day)==day]
    dday = d[(d.get("timestamp",pd.Series(dtype="datetime64[ns]")).dt.date==day)]

    # trade stats
    if not tday.empty:
        tday["pnl"] = (tday["exit"]-tday["entry"]) * tday["qty"] - tday.get("fees",0)
        wins = int((tday["pnl"]>0).sum()); losses=int((tday["pnl"]<0).sum())
        pnl_sum = float(tday["pnl"].sum())
        win_rate = (wins/(wins+losses)*100) if (wins+losses)>0 else 0.0
        best = tday.sort_values("pnl").tail(1)[["ticker","pnl"]].iloc[0].to_dict()
        worst= tday.sort_values("pnl").head(1)[["ticker","pnl"]].iloc[0].to_dict()
    else:
        wins=losses=0; pnl_sum=0.0; win_rate=0.0; best={"ticker":"—","pnl":0}; worst={"ticker":"—","pnl":0}

    lines = [
        f"# Daily Journal — {dstr}",
        "",
        "## Trades",
        f"- Count: {len(tday)} | Wins: {wins} | Losses: {losses} | Win rate: {win_rate:.1f}%",
        f"- PnL (sum): ${pnl_sum:.2f} | Best: {best['ticker']} (${best['pnl']:.2f}) | Worst: {worst['ticker']} (${worst['pnl']:.2f})",
        "",
        "## Decisions",
    ]
    if dday.empty:
        lines.append("- No decisions logged today.")
    else:
        for _, r in dday.iterrows():
            lines.append(f"- {r.get('timestamp','')} | {r.get('ticker','')} → **{r.get('action','')}** | R:R={r.get('reward_risk','')} | Note: {r.get('rationale','')}")
    lines += ["", "## Lessons & Notes", "- "]
    return "\n".join(lines)

def render_auto_journal():
    st.header("Auto-Journal Generator")
    day = st.date_input("Journal date", dt.date.today())
    trades = _load_csv(TRADES_CSV)
    decisions = _load_csv(DECISIONS_CSV)
    md = _mk_summary(day, trades, decisions)

    st.subheader("Preview")
    st.text_area("Markdown", md, height=260)
    path = os.path.join(JOURNAL_DIR, f"{day.isoformat()}.md")

    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Save to /data/journal"):
            with open(path,"w",encoding="utf-8") as f: f.write(md)
            st.success(f"Saved: {path}")
    with c2:
        st.download_button("Download .md", data=md.encode("utf-8"), file_name=f"{day.isoformat()}.md", mime="text/markdown")
    with c3:
        cfg = _load_cfg()
        if st.button("Email me this (uses SMTP config)"):
            ok, info = _safe_send_email(f"[VEGA] Daily Journal {day.isoformat()}", md, _email_cfg(cfg))
            st.success("Email sent.") if ok else st.warning(f"Email failed: {info}")
