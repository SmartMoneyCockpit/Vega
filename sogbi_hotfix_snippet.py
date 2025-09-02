
from __future__ import annotations
import os, json
import streamlit as st
from dataclasses import dataclass

CFG_PATH = "config/stay_get.json"

@dataclass
class Triggers:
    spy_get_in: float = 651.39
    qqq_confirm: float = 576.32
    spy_risk1: float = 638.49
    spy_risk2: float = 632.04

def _load_triggers() -> Triggers:
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            d = json.load(f) or {}
        return Triggers(
            spy_get_in=float(d.get("spy_get_in", 651.39)),
            qqq_confirm=float(d.get("qqq_confirm", 576.32)),
            spy_risk1=float(d.get("spy_risk1", 638.49)),
            spy_risk2=float(d.get("spy_risk2", 632.04)),
        )
    except Exception:
        return Triggers()

def _save_triggers(t: Triggers) -> str:
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "spy_get_in": t.spy_get_in,
            "qqq_confirm": t.qqq_confirm,
            "spy_risk1": t.spy_risk1,
            "spy_risk2": t.spy_risk2,
        }, f, indent=2)
    return CFG_PATH

@dataclass
class Decision:
    regime: str
    details: str

def _decide(spy: float | None, qqq: float | None, t: Triggers) -> Decision:
    if spy is None or qqq is None or spy == 0.0 or qqq == 0.0:
        return Decision("WAIT", "Waiting for SPY/QQQ inputs.")
    if spy >= t.spy_get_in and qqq >= t.qqq_confirm:
        return Decision("GET_BACK_IN", "Both SPY and QQQ above close triggers.")
    if spy <= t.spy_risk2:
        return Decision("RISK_OFF", "SPY below -2% line → escalate hedges.")
    if spy <= t.spy_risk1:
        return Decision("WAIT", "SPY below -1% line → arm starter hedges; wait for close.")
    return Decision("WAIT", "No trigger hit; maintain stance until close.")

def page_stay_out_get_back_in():
    st.markdown("## Stay Out vs Get Back In")
    if "sogbi_state" not in st.session_state:
        st.session_state["sogbi_state"] = {
            "spy": 0.0, "qqq": 0.0, "vix": 0.0, "triggers": _load_triggers()
        }
    S = st.session_state["sogbi_state"]
    t: Triggers = S["triggers"]

    c1, c2 = st.columns([1,1])
    with c1:
        st.subheader("Live Inputs", anchor=False)
        S["spy"] = st.number_input("SPY (live/close)", value=float(S.get("spy", 0.0)), key="sogbi_spy")
        S["qqq"] = st.number_input("QQQ (live/close)", value=float(S.get("qqq", 0.0)), key="sogbi_qqq")
        S["vix"] = st.number_input("VIX (optional)", value=float(S.get("vix", 0.0)), key="sogbi_vix")
        st.caption("Use *closing* values to flip regimes; intraday values only arm risk.")

    with c2:
        st.subheader("Triggers", anchor=False)
        t.spy_get_in = st.number_input("SPY → GET BACK IN (close)", value=float(t.spy_get_in), key="sogbi_t_spy_up")
        t.qqq_confirm = st.number_input("QQQ confirm (close)", value=float(t.qqq_confirm), key="sogbi_t_qqq_up")
        t.spy_risk1 = st.number_input("SPY risk: arm hedges (intraday)", value=float(t.spy_risk1), key="sogbi_t_spy_r1")
        t.spy_risk2 = st.number_input("SPY risk: escalate (intraday)", value=float(t.spy_risk2), key="sogbi_t_spy_r2")
        if st.button("💾 Save triggers", key="sogbi_save"):
            path = _save_triggers(t)
            st.success(f"Saved to {path}")

    st.divider()
    decision = _decide(S["spy"], S["qqq"], t)
    if decision.regime == "GET_BACK_IN":
        st.success("🟢 GET BACK IN — " + decision.details)
    elif decision.regime == "RISK_OFF":
        st.error("🔴 RISK-OFF — " + decision.details)
    else:
        st.warning("🟡 WAIT — " + decision.details)

    with st.expander("Diagnostics"):
        st.json({
            "inputs": {"spy": S["spy"], "qqq": S["qqq"], "vix": S["vix"]},
            "triggers": t.__dict__,
            "session_keys": list(st.session_state.keys()),
        })
