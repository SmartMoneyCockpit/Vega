import json
import streamlit as st
from pathlib import Path

def load_picks_from_json(path: str, region_key: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    # Expect data like {"NA": [...], "EU": [...], "APAC": [...]}
    return data.get(region_key, [])

def seed_session_picks(json_path: str = "templates/sample_picks.json") -> None:
    # Only seed if nothing present
    for region in ("NA","EU","APAC"):
        key = f"{region}_picks"
        if key not in st.session_state:
            st.session_state[key] = load_picks_from_json(json_path, region)
