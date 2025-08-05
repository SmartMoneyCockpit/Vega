
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load the cleaned demo file
df = pd.read_csv("data/trades_demo_NEXT.csv")

# Authenticate with Google Sheets using the fixed service account file
scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("data/gcp_service_account_FIXED.json", scopes)
client = gspread.authorize(credentials)

# Open the spreadsheet and target worksheet
sheet = client.open("COCKPIT")
worksheet = sheet.worksheet("TradeLog")

# Clear the existing data
worksheet.clear()

# Upload the new data (header + all rows)
rows = [df.columns.tolist()] + df.values.tolist()
worksheet.update(rows)

# 🧠