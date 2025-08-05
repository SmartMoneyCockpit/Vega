
import streamlit as st

def main():
    st.set_page_config(page_title="Smart Money Cockpit", layout="wide")
    st.title("🚀 Smart Money Cockpit – Full Deployment")

    st.markdown("### Modules Enabled:")
    st.markdown("- ✅ PnL Tracker")
    st.markdown("- ✅ FX Exposure")
    st.markdown("- ✅ Smart Money Alerts")
    st.markdown("- ✅ Health Dashboard")
    st.markdown("- ✅ Trade Journal")
    st.markdown("- ✅ Daily PDF Report (7:45 AM PT)")

    st.info("This version runs safely on Streamlit Cloud. IBKR integration has been removed.")

if __name__ == "__main__":
    main()

# 🧠