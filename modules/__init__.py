<<<<<<< HEAD

# __init__.py for Smart Money Cockpit modules
# This file allows dynamic importing of modules via app.py

# Optional: pre-imports for IDE indexing or fallback support
from .trade_logger import render as trade_logger
from .daily_briefing import render as daily_briefing
from .etf_dashboard import render as etf_dashboard
from .pdf_generator import render as pdf_generator
from .journal_logger import render as journal_logger
from .strategy_builder import render as strategy_builder
from .health_tracker import render as health_tracker
from .pattern_profiler import render as pattern_profiler
from .guardrails import render as guardrails
from .ai_journal import render as ai_journal
from .vagal_sync import render as vagal_sync
from .auto_hedger import render as auto_hedger
from .preferred_income_tracker import render as preferred_income_tracker
from .spy_contra_tracker import render as spy_contra_tracker
from .macro_micro_dashboard import render as macro_micro_dashboard
from .smart_money_logic import render as smart_money_logic
from .training_tier import render as training_tier
from .boi_playbook import render as boi_playbook
from .bear_mode_tail_risk import render as bear_mode_tail_risk
from .tariff_aware_screener import render as tariff_aware_screener
=======
"""
Subpackage for the Smart Money Cockpit modules.

Each module defines a `render` function that accepts a Streamlit container and
renders its user interface.  Modules may also define helper functions that are
used internally or shared across the application.
"""

from .trade_logger import render as render_trade_logger
from .health_tracker import render as render_health_tracker
from .daily_briefing import render as render_daily_briefing
from .journal_logger import render as render_journal_logger
from .strategy_builder import render as render_strategy_builder
from .pdf_generator import render as render_pdf_generator
from .training_tier import render as render_training_tier
from .macro_micro_dashboard import render as render_macro_micro_dashboard
from .bear_mode_tail_risk import render as render_bear_mode_tail_risk
from .etf_dashboard import render as render_etf_dashboard
from .boj_playbook import render as render_boj_playbook
from .tariff_aware_screener import render as render_tariff_aware_screener
from .preferred_income_tracker import render as render_preferred_income_tracker
from .live_pnl_tracker import render as render_live_pnl_tracker
from .spy_contra_tracker import render as render_spy_contra_tracker
from .smart_money_logic import render as render_smart_money_logic
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410
