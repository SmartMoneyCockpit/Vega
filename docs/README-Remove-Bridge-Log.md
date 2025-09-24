# Remove old Bridge Log page
Run:
```
python scripts/cleanup_bridge_log.py
```
This deletes `pages/93_IBKR_Bridge_Log.py` if present. No changes to `app.py` needed (it doesn't link to this page). Redeploy after running.
