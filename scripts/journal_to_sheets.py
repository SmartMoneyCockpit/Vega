import os, time, json
sid = os.getenv("SHEETS_SPREADSHEET_ID")
sa = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
journal_dir = os.path.join("vault","journal")
os.makedirs(journal_dir, exist_ok=True)
ts = time.strftime("%Y-%m-%d")
if sid and sa:
    with open(os.path.join(journal_dir, f"journal-{ts}.txt"), "w", encoding="utf-8") as f:
        f.write(f"Journal row appended to Google Sheets (simulated) — {ts}\n")
    print("Would append a row to Google Sheets here.")
else:
    with open(os.path.join(journal_dir, f"journal-{ts}.txt"), "w", encoding="utf-8") as f:
        f.write(f"Local Journal (Sheets not configured) — {ts}\n")
    print("Sheets not configured; wrote local journal file.")
