# utils/prefs_bootstrap.py
from utils.load_prefs import load_prefs

# Single shared instance per Streamlit run
prefs = load_prefs()
