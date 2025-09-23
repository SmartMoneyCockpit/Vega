# scripts/cleanup_pages.py
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
KEEP = {"095_IB_Feed_Status.py","096_IBKR_Ticker_ib.py","097_IBKR_Quick_Test_ib.py","098_IBKR_Order_Ticket_ib.py"}
DELETE = ["091_IBKR_Live_Ticker.py","91_IBKR_Live_Ticker.py","090_IB_Feed_Status.py","900_IB_Feed_Status.py"]
def main():
    removed=[]
    for name in DELETE:
        p=PAGES/name
        if p.exists(): p.unlink(); removed.append(name)
    print("[cleanup] removed:", removed or "none")
if __name__=="__main__": main()
