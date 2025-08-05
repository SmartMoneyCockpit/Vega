
import streamlit as st
def main():
    st.header("Pnl Tracker.Py Page")
    st.image("static/assets/animal_2.jpg", width=120)
    st.success("✅ Pnl Tracker.Py is loaded and ready.")
st.subheader("📊 PnL Summary")

if not df.empty:
    trades = df[df['Ticker'].notna()].copy()
    grouped = trades.groupby('Ticker')

    for ticker, group in grouped:
        buys = group[group['Quantity'] > 0]
        sells = group[group['Quantity'] < 0]

        if not buys.empty and not sells.empty:
            avg_buy = (buys['Price'] * buys['Quantity']).sum() / buys['Quantity'].sum()
            avg_sell = (sells['Price'] * sells['Quantity'].abs()).sum() / sells['Quantity'].abs().sum()
            qty = min(buys['Quantity'].sum(), -sells['Quantity'].sum())
            pnl = round((avg_sell - avg_buy) * qty, 2)
            st.success(f"{ticker}: {qty} shares | Buy @ {avg_buy} → Sell @ {avg_sell} | 💰 PnL = ${pnl}")
        else:
            st.warning(f"{ticker} → Not enough data to calculate PnL.")

# 🧠