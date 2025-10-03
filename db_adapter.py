"""db_adapter.py — SQLite Edition (zero setup)
Persists cockpit data in a local SQLite file (default: data/vega.db).

⚠️ On Render: add a Persistent Disk and mount it to a writeable path (e.g., /opt/render/project/src/data)
so the database file survives restarts/redeploys.

Tables created automatically on first run:
- positions(Ticker TEXT, Qty REAL, AvgCost REAL, Last REAL)
- signals(Ticker TEXT, Setup TEXT, Reason TEXT, Country TEXT)
- breadth(Metric TEXT, Value TEXT, Status TEXT)
- rs(Bucket TEXT, RSTrend TEXT)
"""
from __future__ import annotations
import os, sqlite3, contextlib
import pandas as pd

DB_PATH = os.getenv("VEGA_DB_PATH", "data/vega.db")  # override via env if you like

def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS positions (Ticker TEXT PRIMARY KEY, Qty REAL, AvgCost REAL, Last REAL)")
        cur.execute("CREATE TABLE IF NOT EXISTS signals   (Ticker TEXT PRIMARY KEY, Setup TEXT, Reason TEXT, Country TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS breadth   (Metric TEXT PRIMARY KEY, Value TEXT, Status TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS rs        (Bucket TEXT PRIMARY KEY, RSTrend TEXT)")
        con.commit()

def _conn():
    _ensure_db()
    return sqlite3.connect(DB_PATH)

# -------- Loaders (used by the cockpit) --------
def load_positions() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Ticker, Qty, AvgCost as 'Avg Cost', Last FROM positions", con)
    if df.empty:
        # seed demo row so UI isn't blank
        return pd.DataFrame({"Ticker":["HPR.TO"],"Qty":[1000],"Avg Cost":[25.0],"Last":[25.4]})
    return df

def load_signals() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Ticker, Setup, Reason, Country FROM signals", con)
    if df.empty:
        return pd.DataFrame({"Ticker":["SPXU"],"Setup":["Buy Today"],"Reason":["Hedge basket"],"Country":["USA"]})
    return df

def load_breadth() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Metric, Value, Status FROM breadth", con)
    if df.empty:
        return pd.DataFrame({"Metric":["VIX"],"Value":["18.7"],"Status":["Neutral"]})
    return df

def load_rs() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query("SELECT Bucket, RSTrend as 'RS Trend' FROM rs", con)
    if df.empty:
        return pd.DataFrame({"Bucket":["USA"],"RS Trend":["🟡"]})
    return df

# -------- Simple upsert helpers (used by admin page) --------
def upsert_positions(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM positions")
        for _, r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO positions(Ticker,Qty,AvgCost,Last) VALUES(?,?,?,?)",
                        (str(r["Ticker"]).strip(), float(r["Qty"]), float(r["Avg Cost"]), float(r["Last"])))
        con.commit()

def upsert_signals(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM signals")
        for _, r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO signals(Ticker,Setup,Reason,Country) VALUES(?,?,?,?)",
                        (str(r.get("Ticker","")), str(r.get("Setup","")), str(r.get("Reason","")), str(r.get("Country",""))))
        con.commit()

def upsert_breadth(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM breadth")
        for _, r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO breadth(Metric,Value,Status) VALUES(?,?,?)",
                        (str(r.get("Metric","")), str(r.get("Value","")), str(r.get("Status",""))))
        con.commit()

def upsert_rs(df: pd.DataFrame) -> None:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM rs")
        for _, r in df.iterrows():
            cur.execute("INSERT OR REPLACE INTO rs(Bucket,RSTrend) VALUES(?,?)",
                        (str(r.get("Bucket","")), str(r.get("RS Trend",""))))
        con.commit()
