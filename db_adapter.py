from __future__ import annotations
import os, sqlite3, contextlib
from datetime import datetime as _dt
from typing import Iterable, Optional
import pandas as pd

DB_PATH = os.getenv("VEGA_DB_PATH", "data/vega.db")

def _ensure_tables() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS positions (Ticker TEXT PRIMARY KEY, Qty REAL, AvgCost REAL, Last REAL)")
        cur.execute("CREATE TABLE IF NOT EXISTS signals (Ticker TEXT PRIMARY KEY, Setup TEXT, Reason TEXT, Country TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS breadth (Metric TEXT PRIMARY KEY, Value TEXT, Status TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS rs (Bucket TEXT PRIMARY KEY, RSTrend TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS rs_history (dt TEXT, Bucket TEXT, Value REAL, PRIMARY KEY (dt, Bucket))")
        con.commit()

def _conn(): _ensure_tables(); return sqlite3.connect(DB_PATH)

# ---- RS mapping (custom) ----
def map_trend_to_value(trend: str) -> float:
    t = (trend or "").strip()
    return {
        "🟢": 1.4, "Green": 1.4,
        "🟠": 1.2, "Orange": 1.2,
        "🟡": 1.0, "Yellow": 1.0,
        "🔴": 0.8, "Red": 0.8
    }.get(t, 1.0)

# ---- Loaders ----
def load_positions() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Ticker, Qty, AvgCost as 'Avg Cost', Last FROM positions", con)
    return df if not df.empty else pd.DataFrame({"Ticker":["HPR.TO"],"Qty":[1000],"Avg Cost":[25.0],"Last":[25.4]})

def load_signals() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Ticker, Setup, Reason, Country FROM signals", con)
    return df if not df.empty else pd.DataFrame({"Ticker":["SPXU"],"Setup":["Buy Today"],"Reason":["Hedge basket"],"Country":["USA"]})

def load_breadth() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Metric, Value, Status FROM breadth", con)
    return df if not df.empty else pd.DataFrame({"Metric":["VIX"],"Value":["18.7"],"Status":["Neutral"]})

def load_rs() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Bucket, RSTrend as 'RS Trend' FROM rs", con)
    return df if not df.empty else pd.DataFrame({"Bucket":["USA"],"RS Trend":["🟡"]})

# ---- Upserts ----
def upsert_positions(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur=con.cursor(); cur.execute("DELETE FROM positions")
        for _,r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO positions(Ticker,Qty,AvgCost,Last) VALUES(?,?,?,?)",(str(r["Ticker"]).strip(), float(r["Qty"]), float(r["Avg Cost"]), float(r["Last"])))
        con.commit()

def upsert_signals(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur=con.cursor(); cur.execute("DELETE FROM signals")
        for _,r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO signals(Ticker,Setup,Reason,Country) VALUES(?,?,?,?)",(str(r.get("Ticker","")),str(r.get("Setup","")),str(r.get("Reason","")),str(r.get("Country",""))))
        con.commit()

def upsert_breadth(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur=con.cursor(); cur.execute("DELETE FROM breadth")
        for _,r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO breadth(Metric,Value,Status) VALUES(?,?,?)",(str(r.get("Metric","")),str(r.get("Value","")),str(r.get("Status",""))))
        con.commit()

def upsert_rs(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur=con.cursor(); cur.execute("DELETE FROM rs")
        for _,r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO rs(Bucket,RSTrend) VALUES(?,?)",(str(r.get("Bucket","")),str(r.get("RS Trend",""))))
        con.commit()

# ---- RS History ----
def rs_history_append_from_current(rs_df: pd.DataFrame, when: Optional[str]=None) -> None:
    if rs_df is None or rs_df.empty: return
    if when is None: when = _dt.now().strftime("%Y-%m-%d")
    rows = []
    for _, r in rs_df.iterrows():
        bucket = str(r.get("Bucket","")).strip()
        trend  = str(r.get("RS Trend","")).strip()
        if not bucket: continue
        rows.append((when, bucket, float(map_trend_to_value(trend))))
    with _conn() as con:
        cur = con.cursor()
        for dt,b,v in rows:
            cur.execute("INSERT OR REPLACE INTO rs_history(dt,Bucket,Value) VALUES(?,?,?)",(dt,b,v))
        con.commit()

def load_rs_history(buckets: Optional[Iterable[str]]=None, start: Optional[str]=None, end: Optional[str]=None) -> pd.DataFrame:
    q = "SELECT dt, Bucket, Value FROM rs_history"
    clauses, params = [], []
    if buckets:
        placeholders = ",".join(["?"]*len(list(buckets)))
        clauses.append(f"Bucket IN ({placeholders})"); params.extend(list(buckets))
    if start: clauses.append("dt >= ?"); params.append(start)
    if end: clauses.append("dt <= ?"); params.append(end)
    if clauses: q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY dt ASC, Bucket ASC"
    with _conn() as con:
        return pd.read_sql_query(q, con, params=params)
