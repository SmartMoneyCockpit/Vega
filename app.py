import streamlit as st
import os, re, sys

# --- Vega safety check: prevent duplicate Streamlit page slugs ---
def infer_slug_from_filename(path: str) -> str:
    """Approximate Streamlit's slug: strip numeric prefixes then slugify."""
    base = os.path.splitext(os.path.basename(path))[0]
    base = re.sub(r'^\d+[_-]*', '', base)          # drop leading numbers
    base = re.sub(r'[^0-9A-Za-z]+', '-', base)     # non-alnum -> hyphen
    base = re.sub(r'-+', '-', base).strip('-')     # collapse hyphens
    return base.lower()

if os.path.isdir("pages"):
    page_files = [
        os.path.join("pages", f)
        for f in os.listdir("pages")
        if f.endswith(".py") and f != "__init__.py"
    ]
    slug_map = {}
    for f in page_files:
        slug = infer_slug_from_filename(f)
        slug_map.setdefault(slug, []).append(f)

    dup = {s: fs for s, fs in slug_map.items() if len(fs) > 1}
    if dup:
        lines = "\n".join(f"  /{s}  ->  {', '.join(fs)}" for s, fs in sorted(dup.items()))
        sys.exit(
            "[BOOT BLOCKED] Duplicate page URL paths detected in pages/:\n"
            f"{lines}\n\nFix by renaming or removing duplicates."
        )
# --- end safety check ---

st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')

st.page_link('pages/00_Home.py', label='🏠 Home', icon='🏠')
st.page_link('pages/095_IB_Feed_Status.py', label='📡 IB Feed Status')
st.page_link('pages/096_IBKR_Ticker_ib.py', label='⏱️ IBKR Ticker (ib_insync)')
st.page_link('pages/097_IBKR_Quick_Test_ib.py', label='🧪 IBKR Quick Test (ib_insync)')
st.page_link('pages/098_IBKR_Order_Ticket_ib.py', label='🧾 IBKR Order Ticket (ib_insync)')
st.page_link('pages/101_North_America.py', label='🌎 North America')
st.page_link('pages/102_Europe.py', label='🌍 Europe')
st.page_link('pages/103_APAC.py', label='🌏 APAC')
