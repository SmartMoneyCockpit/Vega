import os, time
from reportlab.pdfgen import canvas
vault = os.path.join("vault","exports")
os.makedirs(vault, exist_ok=True)
ts = time.strftime("%Y%m%d-%H%M%S")
pdf_path = os.path.join(vault, f"daily-report-{ts}.pdf")
c = canvas.Canvas(pdf_path)
c.setFont("Helvetica-Bold", 16); c.drawString(72, 760, "Vega Daily Report")
c.setFont("Helvetica", 10); c.drawString(72, 740, f"Timestamp: {ts}")
c.drawString(72, 720, "Includes: Breadth summary, VV/ETF signals, Guardrails alerts, Journal note (stubs).")
c.save()
print("Daily report exported:", pdf_path)
