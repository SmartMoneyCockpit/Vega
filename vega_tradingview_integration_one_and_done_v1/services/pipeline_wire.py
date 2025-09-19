"""Helpers to publish picks from your pipeline into the Streamlit UI."""
import streamlit as st
from typing import Iterable

REQUIRED_KEYS = {"symbol","exchange","side","entry","stop","target1","target2","rr","reason_tags","notes"}

def _coerce_row(d: dict) -> dict:
    row = {k: d.get(k, "") for k in REQUIRED_KEYS}
    if isinstance(row.get("symbol"), str):
        row["symbol"] = row["symbol"].strip().upper()
    if isinstance(row.get("exchange"), str):
        row["exchange"] = row["exchange"].strip().upper()
    return row

def publish_picks(region: str, rows: Iterable[dict]) -> None:
    region = region.upper()
    key = f"{region}_picks"
    st.session_state[key] = [_coerce_row(r) for r in rows]
