import os, sys, subprocess
import streamlit as st
import httpx
import pathlib

# --- robust bridge config import ---
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from config.ib_bridge_client import get_bridge_url, get_bridge_api_key  # type: ignore
except Exception:
    def get_bridge_url():
        scheme = os.getenv("BRIDGE_SCHEME", "http")
        host   = os.getenv("IB_HOST", "127.0.0.1")
        port   = os.getenv("BRIDGE_PORT", "8088")
        return f"{scheme}://{host}:{port}"

    def get_bridge_api_key():
        return os.getenv("IB_BRIDGE_API_KEY", "")

# --- page setup ---
st.set_page_config(page_title="Scan / Morning Report", layout="wide")
st.header("🔎 Scan / Morning Report – On-Demand")

base = get_bridge_url().rstrip("/")
api_key = get_bridge_api_key()
headers = {"x-api-key": api_key} if api_key else {}

def bridge_ok():
    try:
        r = httpx.get(f"{base}/health", headers=headers, timeout=3)
        r.raise_for_status()
        return True
    except Exception:
        return False

if st.button("▶️ Run Scan + Morning Report", use_container_width=True):
    if not bridge_ok():
        st.warning("IBKR Bridge not reachable. Log into IBKR on the VPS, then try again.")
    else:
        with st.status("Running scanners and building the morning report…", expanded=True) as s:
            cmd = [
                sys.executable,
                "scripts/reports/generate_morning_report.py",
                "--region", "North America",
                "--tz", "America/Los_Angeles",
                "--out", "reports/na/morning_report.md",
            ]
            try:
                subprocess.run(cmd, check=True)
                s.update(label="Done!", state="complete")
                st.success("Scan complete ✅  Saved to reports/na/morning_report.md")
            except subprocess.CalledProcessError as e:
                st.error(f"Report generation failed: {e}")
