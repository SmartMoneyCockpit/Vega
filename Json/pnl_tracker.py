import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

def main():
    st.header("PnL Tracker:Py Page")
    st.image("static/assets/animal_2.jpg", width=120)
    st.success("✅ PnL Tracker:Py is loaded and ready.")
    st.subheader("📈 PnL Summary")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("COCKPIT").worksheet("TradeLog")
    df = get_as_dataframe(sheet).dropna(how='all')

    if not df.empty:
        trades = df[df['Ticker'].notna()].copy()
        grouped = trades.groupby('Ticker')

        for ticker, group in grouped:
            buys = group[group['Quantity'] > 0]
            sells = group[group['Quantity'] < 0]

            if not buys.empty and not sells.empty:
                avg_buy = (buys['Price'] * buys['Quantity']).sum() / buys['Quantity'].sum()
                avg_sell = (sells['Price'] * sells['Quantity'].abs()).sum() / sells['Quantity'].abs().sum()
                qty = min(buys['Quantity'].sum(), sells['Quantity'].abs().sum())
                pnl = round((avg_sell - avg_buy) * qty, 2)
                st.success(f"{ticker}: {qty} shares | Buy @ {avg_buy} | Sell @ {avg_sell} | 📊 PnL = {pnl}")
            else:
                st.warning(f"{ticker}: Not enough data to calculate PnL.")
    else:
        st.warning("No trade data found.")

if __name__ == "__main__":
    main()
