import streamlit as st
from pathlib import Path
import pandas as pd
import importlib

from modules import (
    render_trade_logger,
    render_smart_money_logic,
    render_health_tracker,
    render_daily_briefing,
    render_journal_logger,
    render_strategy_builder,
    render_pdf_generator,
    render_training_tier,
    render_macro_micro_dashboard,
    render_bear_mode_tail_risk,
    render_etf_dashboard,
    render_boj_playbook,
    render_tariff_aware_screener,
    render_preferred_income_tracker,
    render_live_pnl_tracker,
    render_spy_contra_tracker,
)
from utils import google_sheets, ibkr

def get_module_statuses() -> pd.DataFrame:
    modules = [
        "Trade Logger",
        "Smart Money Logic",
        "Health Tracker",
        "Daily Morning Briefing",
        "Journal Logger",
        "Strategy Builder",
        "PDF Generator",
        "Training Tier",
        "Macro/Micro Dashboard",
        "Bear Mode / Tail‑Risk",
        "ETF Dashboard",
        "BoJ Rate Playbook",
        "Tariff‑Aware Screener",
        "Preferred Income Tracker",
        "Live PnL Tracker",
        "SPY & Contra Tracker",
    ]
    statuses = []
    sheet_ok = google_sheets.get_sheet() is not None
    ib_ok = ibkr.connect() is not None
    for m in modules:
        if m == "Live PnL Tracker":
            ready = ib_ok
        else:
            ready = True
        statuses.append({"Module": m, "Status": "Ready" if ready else "Offline"})
    return pd.DataFrame(statuses)

def load_image(image_name: str):
    img_path = Path(__file__).resolve().parent / "assets" / image_name
    if img_path.exists():
        return open(img_path, "rb").read()
    return None

def main() -> None:
    st.set_page_config(page_title="Smart Money Cockpit", layout="wide")
    coin_img = load_image("coin.png")
    if coin_img:
        st.sidebar.image(coin_img, use_column_width=True)
    st.sidebar.title("Smart Money Cockpit")

    module_names = [
        "Trade Logger",
        "Smart Money Logic",
        "Health Tracker",
        "Daily Morning Briefing",
        "Journal Logger",
        "Strategy Builder",
        "PDF Generator",
        "Training Tier",
        "Macro/Micro Dashboard",
        "Bear Mode / Tail‑Risk",
        "ETF Dashboard",
        "BoJ Rate Playbook",
        "Tariff‑Aware Screener",
        "Preferred Income Tracker",
        "Live PnL Tracker",
        "SPY & Contra Tracker",
    ]
    choice = st.sidebar.selectbox("Choose a module", module_names)

    if st.sidebar.checkbox("Show module status", value=False):
        status_df = get_module_statuses()
        st.sidebar.dataframe(status_df, height=300)

    if choice == "Trade Logger":
        render_trade_logger()
    elif choice == "Smart Money Logic":
        render_smart_money_logic()
    elif choice == "Health Tracker":
        render_health_tracker()
    elif choice == "Daily Morning Briefing":
        render_daily_briefing()
    elif choice == "Journal Logger":
        render_journal_logger()
    elif choice == "Strategy Builder":
        render_strategy_builder()
    elif choice == "PDF Generator":
        render_pdf_generator()
    elif choice == "Training Tier":
        render_training_tier()
    elif choice == "Macro/Micro Dashboard":
        render_macro_micro_dashboard()
    elif choice == "Bear Mode / Tail‑Risk":
        render_bear_mode_tail_risk()
    elif choice == "ETF Dashboard":
        render_etf_dashboard()
    elif choice == "BoJ Rate Playbook":
        render_boj_playbook()
    elif choice == "Tariff‑Aware Screener":
        render_tariff_aware_screener()
    elif choice == "Preferred Income Tracker":
        render_preferred_income_tracker()
    elif choice == "Live PnL Tracker":
        render_live_pnl_tracker()
    elif choice == "SPY & Contra Tracker":
        render_spy_contra_tracker()
    else:
        st.write("Please select a module from the sidebar.")

if __name__ == "__main__":
    main()
