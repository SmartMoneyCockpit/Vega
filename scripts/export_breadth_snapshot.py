import os, time
from reportlab.pdfgen import canvas
vault = os.path.join("vault","snapshots")
os.makedirs(vault, exist_ok=True)
ts = time.strftime("%Y%m%d-%H%M%S")
pdf_path = os.path.join(vault, f"breadth-{ts}.pdf")
c = canvas.Canvas(pdf_path)
c.setFont("Helvetica", 14); c.drawString(72, 720, "Vega — Breadth Snapshot")
c.setFont("Helvetica", 10); c.drawString(72, 700, f"Timestamp: {ts}")
c.drawString(72, 680, "Server-side stub capture.")
c.save()
print("Snapshot exported:", pdf_path)
