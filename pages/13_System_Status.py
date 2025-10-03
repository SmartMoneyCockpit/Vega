import os, glob, math, json, datetime as dt
import streamlit as st

from app_auth import login_gate
if not login_gate(): pass

st.set_page_config(page_title="System Status", layout="wide")
st.title("Vega System Status")

# ---- Helpers ----
def human_bytes(n: int) -> str:
    if n is None: return "0 B"
    units = ["B","KB","MB","GB","TB"]
    s = float(n); i = 0
    while s >= 1024 and i < len(units)-1:
        s /= 1024.0; i += 1
    return f"{s:.1f} {units[i]}"

def dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    return total

def newest_mtime(pattern: str):
    files = glob.glob(pattern)
    if not files: return None, None
    newest = max(files, key=os.path.getmtime)
    ts = dt.datetime.fromtimestamp(os.path.getmtime(newest)).strftime("%Y-%m-%d %H:%M:%S")
    return newest, ts

# ---- Disk usage ----
snap_dir = "snapshots"
alerts_dir = "alerts"
snap_bytes = dir_size(snap_dir) if os.path.isdir(snap_dir) else 0
alerts_bytes = dir_size(alerts_dir) if os.path.isdir(alerts_dir) else 0

st.subheader("Disk Usage")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Snapshots folder", human_bytes(snap_bytes))
with c2:
    st.metric("Alerts folder", human_bytes(alerts_bytes))
with c3:
    total = snap_bytes + alerts_bytes
    st.metric("Total (snapshots + alerts)", human_bytes(total))

st.caption("Tip: Rotation runs daily and will prune files older than your retention and enforce the size cap.")

# ---- Last run times inferred from artifacts ----
st.subheader("Last Run Times (inferred)")
colA, colB = st.columns(2)

with colA:
    pos_file, pos_ts = newest_mtime(os.path.join(snap_dir, "positions_*.csv"))
    sig_file, sig_ts = newest_mtime(os.path.join(snap_dir, "signals_*.csv"))
    br_file, br_ts   = newest_mtime(os.path.join(snap_dir, "breadth_*.csv"))
    rs_file, rs_ts   = newest_mtime(os.path.join(snap_dir, "rs_*.csv"))
    zip_file, zip_ts = newest_mtime(os.path.join(snap_dir, "digest_*.zip"))
    meta_file, meta_ts = newest_mtime(os.path.join(snap_dir, "meta_*.json"))

    st.write("**Export Job Artifacts**")
    st.write(f"- positions CSV: {pos_ts or '—'}")
    st.write(f"- signals CSV: {sig_ts or '—'}")
    st.write(f"- breadth CSV: {br_ts or '—'}")
    st.write(f"- rs CSV: {rs_ts or '—'}")
    st.write(f"- digest ZIP: {zip_ts or '—'}")
    st.write(f"- meta JSON: {meta_ts or '—'}")

with colB:
    breadth_png, breadth_png_ts = newest_mtime(os.path.join(snap_dir, "breadth_*.png"))
    sector_json, sector_json_ts = newest_mtime(os.path.join(alerts_dir, "sector_flips.json"))
    st.write("**Other Artifacts**")
    st.write(f"- breadth PNG snapshot: {breadth_png_ts or '—'}")
    st.write(f"- sector_flips.json: {sector_json_ts or '—'}")

st.divider()

# ---- Quick actions ----
st.subheader("Quick Actions")
colX, colY = st.columns(2)
with colX:
    if st.button("Run Export Now (ad‑hoc)"):
        try:
            import scripts.export_digest as exp
            exp  # noqa
            st.success("Export script imported; scheduled job will write artifacts on next run.")
            st.info("For an immediate write in this session, run the script in your Render job or a local shell.")
        except Exception as e:
            st.error(f"Could not import export script: {e}")

with colY:
    if st.button("Rotate Now (ad‑hoc)"):
        try:
            import scripts.rotate_snapshots as rot
            rot.main()
            st.success("Rotation complete. Refresh to see updated disk usage.")
        except Exception as e:
            st.error(f"Rotation error: {e}")
