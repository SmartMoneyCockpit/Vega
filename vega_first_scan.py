# vega_first_scan.py
# First end-to-end scan: Watchlist (Sheets) -> IBKR quotes -> Log (Sheets)

import os, sys, time, datetime as dt
from dotenv import load_dotenv

load_dotenv()

IB_HOST     = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT     = int(os.getenv("IB_PORT", "7496"))  # live default
IB_CLIENTID = int(os.getenv("IB_CLIENT_ID", "1"))

WATCH_TAB   = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", "NA_Watch")
LOG_TAB     = os.getenv("GOOGLE_SHEET_LOG_TAB", "NA_TradeLog")

# ---- Sheets helper (your file) ----
import sheets_client as sc

# ---- IBKR ----
from ib_insync import IB, Stock

def parse_contract(symbol: str):
    s = symbol.strip().upper()
    # Basic symbol parsing with simple market suffix handling
    if s.endswith(".TO"):
        return Stock(s.replace(".TO", ""), "SMART", "CAD")
    elif s.endswith(".MX"):
        return Stock(s.replace(".MX", ""), "SMART", "MXN")
    else:
        return Stock(s, "SMART", "USD")

def read_watchlist_tickers(tab: str):
    rows = sc.read_range(f"{tab}!A1:Z2000")  # expect headers in row 1
    if not rows:
        return []

    headers = [h.strip() for h in rows[0]]
    # Prefer a column literally named "Ticker"
    if "Ticker" in headers:
        idx = headers.index("Ticker")
        data_rows = rows[1:]
        syms = [r[idx].strip() for r in data_rows if len(r) > idx and r[idx].strip()]
        return list(dict.fromkeys(syms))  # de-dup, keep order

    # Fallback: first column
    syms = [r[0].strip() for r in rows[1:] if r and r[0].strip()]
    return list(dict.fromkeys(syms))

def main():
    print(f"Reading watchlist from tab: {WATCH_TAB}")
    tickers = read_watchlist_tickers(WATCH_TAB)
    if not tickers:
        print("No tickers found. Add symbols to your Watchlist tab (column 'Ticker').")
        sys.exit(0)

    print(f"Found {len(tickers)} tickers:", ", ".join(tickers[:20]) + ("..." if len(tickers) > 20 else ""))

    # Ensure log tab exists and has headers
    sc.ensure_tab(LOG_TAB, ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"])

    ib = IB()
    print(f"Connecting IBKR {IB_HOST}:{IB_PORT} clientId={IB_CLIENTID} ...")
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID)
    if not ib.isConnected():
        print("❌ IBKR connection failed.")
        sys.exit(1)
    print("✅ IBKR connected.")

    # Request quotes
    for sym in tickers:
        contract = parse_contract(sym)
        try:
            ib.qualifyContracts(contract)
            ticker = ib.reqMktData(contract, "", False, False)
            ib.sleep(2.0)  # small delay to receive fields
            ts = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            last = ticker.last or 0.0
            bid  = ticker.bid  or 0.0
            ask  = ticker.ask  or 0.0
            vol  = int(ticker.volume or 0)

            # Append a lightweight scan row into your log tab
            sc.append_trade_log(
                [ts, "SCAN", sym, "", "", last, f"bid={bid} ask={ask} vol={vol}", "", "", "", "", "", "scan", "ibkr"],
                tab_name=LOG_TAB
            )
            print(f"Logged {sym}: last={last} bid={bid} ask={ask} vol={vol}")
        except Exception as e:
            print(f"⚠️ {sym}: {e}")

    ib.disconnect()
    print("🔌 IBKR disconnected")
    print(f"✅ Done. Open your Google Sheet → '{LOG_TAB}' to see the new rows.")

if __name__ == "__main__":
    main()
