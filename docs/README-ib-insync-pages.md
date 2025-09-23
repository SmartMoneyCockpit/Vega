# IBKR ib_insync Pages (replace old HTTP bridge)

Adds:
- `pages/097_IBKR_Quick_Test_ib.py` (gets a quote via ib_insync)
- `pages/098_IBKR_Order_Ticket_ib.py` (simple MKT/LMT ticket via ib_insync, safety checkbox)
- Updates `app.py` links to surface both pages

Optional cleanup (removes old HTTP pages):
```
python scripts/cleanup_ib_http_pages.py
```
This deletes `pages/90_IBKR_Quick_Test.py` and `pages/92_IBKR_Order_Ticket.py`.
