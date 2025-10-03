# --- RS history support (adds a time series for plotting) ---
# Creates table if not exists: rs_history(dt TEXT, Bucket TEXT, Value REAL)
# Value is a numeric mapped trend score (e.g., 🟢=1.2, 🟡=1.0, 🟠=0.9, 🔴=0.8)
import sqlite3, contextlib, os, pandas as pd, datetime as _dt

DB_PATH = os.getenv("VEGA_DB_PATH", "data/vega.db")

def _ensure_rs_history():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS rs_history (dt TEXT, Bucket TEXT, Value REAL, PRIMARY KEY (dt, Bucket))")
        con.commit()

def map_trend_to_value(trend: str) -> float:
    t = (trend or "").strip()
    return {
        "🟢": 1.2, "Green": 1.2,
        "🟡": 1.0, "Yellow": 1.0,
        "🟠": 0.9, "Orange": 0.9,
        "🔴": 0.8, "Red": 0.8
    }.get(t, 1.0)

def rs_history_append_from_current(rs_df: pd.DataFrame, when: str | None = None) -> None:
    """Append current RS snapshot to rs_history with dt timestamp (YYYY-MM-DD)."""
    if rs_df is None or rs_df.empty:
        return
    _ensure_rs_history()
    if when is None:
        when = _dt.datetime.now().strftime("%Y-%m-%d")
    rows = []
    for _, r in rs_df.iterrows():
        bucket = str(r.get("Bucket","")).strip()
        trend  = str(r.get("RS Trend","")).strip()
        val    = map_trend_to_value(trend)
        if bucket:
            rows.append((when, bucket, float(val)))
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        for dt, bucket, val in rows:
            cur.execute("INSERT OR REPLACE INTO rs_history(dt,Bucket,Value) VALUES(?,?,?)", (dt, bucket, val))
        con.commit()

def load_rs_history(buckets=None, start=None, end=None) -> pd.DataFrame:
    "Return columns: dt, Bucket, Value. dt is YYYY-MM-DD string."
    _ensure_rs_history()
    q = "SELECT dt, Bucket, Value FROM rs_history"
    clauses = []
    params = []
    if buckets:
        placeholders = ",".join(["?"]*len(buckets))
        clauses.append(f"Bucket IN ({placeholders})")
        params.extend(buckets)
    if start:
        clauses.append("dt >= ?"); params.append(start)
    if end:
        clauses.append("dt <= ?"); params.append(end)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY dt ASC, Bucket ASC"
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(q, con, params=params)
