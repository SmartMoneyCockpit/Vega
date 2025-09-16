"""
Sector Flip Alerts — polls sector data and emits in-app alerts.
Stub implementation fits local/offline demo; replace data fetch with providers.
"""
from datetime import datetime
import pandas as pd

def check_flips(df, threshold=0.006):
    # Basic rule: any sector crossing +/- threshold triggers a flip label
    flips = []
    for _, row in df.iterrows():
        chg = row.get("Change%", 0) / 100 if abs(row.get("Change%", 0)) > 1 else row.get("Change%", 0)
        if chg >= threshold:
            flips.append((row["Sector"], "🟢 Buy Today"))
        elif chg <= -threshold:
            flips.append((row["Sector"], "🔴 Avoid"))
    return flips

def render(st, sector_df, settings):
    st.subheader("Sector Flip Alerts")
    flips = check_flips(sector_df, threshold=settings.get("alerts",{}).get("sector_flip",{}).get("rel_change_threshold",0.006))
    if flips:
        for s, status in flips:
            st.success(f"{datetime.now().strftime('%H:%M')} — {s}: {status}")
    else:
        st.info("No sector flips at the moment.")
