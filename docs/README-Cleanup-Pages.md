# Cleanup for duplicate Streamlit pages

Run this once from repo root (Render Shell or locally):

```
python scripts/cleanup_pages.py
```

It deletes these duplicates if present:
- pages/091_IBKR_Live_Ticker.py
- pages/91_IBKR_Live_Ticker.py
- pages/090_IB_Feed_Status.py
- pages/900_IB_Feed_Status.py

It keeps:
- pages/095_IB_Feed_Status.py
- pages/096_IBKR_Ticker_ib.py

After running, redeploy your service.
