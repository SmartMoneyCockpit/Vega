
"""
Defines the watchlist columns to align with the latest Vega rules.
Use this to construct your Streamlit AgGrid or DataFrame schema.
"""
COLUMNS = [
    "Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit","Price",
    "% to Entry","R to Stop","R to Target","Badges",
    # New required fields per user rules:
    "Trade Now vs Wait","Smart Money Grade","Benchmark RS","Breadth Snapshot",
    "Earnings Date (D-#)","No-Buy Window","FX Sensitivity",
    # Canada-specific:
    "Tariff Exposure Grade","USMCA","Action Plan",
]
