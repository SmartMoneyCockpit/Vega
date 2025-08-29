from __future__ import annotations
import streamlit as st
from .engine import Triggers, Inputs, decide
from .config import load_triggers, save_triggers

KEY = "stay_get_state_v1"
PFX = "stayget"

def _get_state():
    if KEY not in st.session_state:
        st.session_state[KEY] = {
            "spy": 0.0,
            "qqq": 0.0,
            "vix": 0.0,
            "triggers": load_triggers(),
        }
    return st.session_state[KEY]

def render():
    st.header("Stay Out vs Get Back In", anchor=False)
    state = _get_state()

    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("Live Inputs", anchor=False)
        state["spy"] = st.number_input("SPY (live/close)", value=float(state.get("spy", 0.0)), key=f"{PFX}_spy")
        state["qqq"] = st.number_input("QQQ (live/close)", value=float(state.get("qqq", 0.0)), key=f"{PFX}_qqq")
        state["vix"] = st.number_input("VIX (optional)", value=float(state.get("vix", 0.0)), key=f"{PFX}_vix")
        st.caption("Use closing values to flip regimes; intraday values only arm risk.")

    with col2:
        st.subheader("Triggers", anchor=False)
        t: Triggers = state["triggers"]
        t.spy_get_in = st.number_input("SPY → GET BACK IN (close)", value=float(t.spy_get_in), key=f"{PFX}_t_spy_up")
        t.qqq_confirm = st.number_input("QQQ confirm (close)", value=float(t.qqq_confirm), key=f"{PFX}_t_qqq_up")
        t.spy_risk1 = st.number_input("SPY risk: arm hedges (intraday)", value=float(t.spy_risk1), key=f"{PFX}_t_spy_r1")
        t.spy_risk2 = st.number_input("SPY risk: escalate (intraday)", value=float(t.spy_risk2), key=f"{PFX}_t_spy_r2")
        if st.button("💾 Save triggers", key=f"{PFX}_save"):
            path = save_triggers(t)
            st.success(f"Saved to {path}")

    st.divider()
    decision = decide(Inputs(spy=state["spy"], qqq=state["qqq"], vix=state["vix"]), state["triggers"])

    if decision.regime == "GET_BACK_IN":
        st.success("🟢 GET BACK IN — " + decision.details)
    elif decision.regime == "RISK_OFF":
        st.error("🔴 RISK-OFF — " + decision.details)
    else:
        st.warning("🟡 WAIT — " + decision.details)

    with st.expander("Diagnostics (dev)"):
        st.json({
            "inputs": {"spy": state["spy"], "qqq": state["qqq"], "vix": state["vix"]},
            "triggers": state["triggers"].__dict__,
            "session_keys": list(st.session_state.keys()),
        })
