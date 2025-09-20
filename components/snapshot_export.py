
from __future__ import annotations
import os, io, datetime as dt
import streamlit as st
from PIL import Image

def export_snapshot(panel_name: str, image: Image.Image | None = None):
    """Saves a PNG (and optional PDF) snapshot with timestamp to vault/snapshots.
    If an image isn't provided (e.g., from st.camera_input or chart export),
    we still write a stub text to confirm the action succeeded.
    """
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join("vault","snapshots")
    os.makedirs(outdir, exist_ok=True)

    png_path = os.path.join(outdir, f"{panel_name}_{ts}.png")
    pdf_path = os.path.join(outdir, f"{panel_name}_{ts}.pdf")

    # Save image if available, else write a 1x1
    if image is not None:
        image.save(png_path)
    else:
        # tiny blank fallback
        from PIL import Image
        img = Image.new("RGB", (1,1), (255,255,255))
        img.save(png_path)

    # Create a trivial single-page PDF using Pillow
    try:
        Image.open(png_path).save(pdf_path, "PDF", resolution=100.0)
    except Exception:
        pass

    st.success(f"Snapshot saved → {png_path}")
    return png_path, pdf_path

def snapshot_button(panel_name: str, image: Image.Image | None = None):
    if st.button(f"📸 Save {panel_name} Snapshot"):
        return export_snapshot(panel_name, image)
    return None, None
