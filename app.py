# Root app.py — forward to src/app.py so Render's startCommand works.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import app  # noqa: F401  (executes Streamlit layout defined in src/app.py)
