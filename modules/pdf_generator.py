"""
PDF Generator Module
-------------------

Generate PDF reports from stored data.  Users can choose which dataset to
export (journal entries, strategies, trades or health logs) and optionally
filter by date range.  The module uses `reportlab` to build a simple
multi‑page PDF and makes it available for download.
"""

import io
import datetime
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(table: str) -> pd.DataFrame:
    file_map = {
        "Journal": "journal.csv",
        "Strategies": "strategies.csv",
        "Trades": "trades.csv",
        "Health": "health.csv",
    }
    csv_file = DATA_DIR / file_map.get(table, "")
    if csv_file.exists():
        return pd.read_csv(csv_file)
    return pd.DataFrame()


def build_pdf(title: str, df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements: List = []
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))
    if df.empty:
        elements.append(Paragraph("No data available.", styles["Normal"]))
    else:
        # Convert DataFrame to a list of lists for Table
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def render() -> None:
    st.subheader("📄 PDF Generator")
    st.write("Export your data to a PDF report.")
    table = st.selectbox("Select dataset", ["Journal", "Strategies", "Trades", "Health"])
    start_date = st.date_input("Start date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = st.date_input("End date", datetime.date.today())
    if start_date > end_date:
        st.warning("Start date must be before end date.")
        return
    if st.button("Generate PDF"):
        df = load_data(table)
        # Filter by date column if exists
        if not df.empty and "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
            df = df.loc[mask]
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        pdf_bytes = build_pdf(f"{table} Report ({start_date} to {end_date})", df)
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"{table}_report_{start_date}_{end_date}.pdf",
            mime="application/pdf",
        )
        )
