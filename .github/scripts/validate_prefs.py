import sys, yaml, json, os

REQUIRED_TOP = [
  "github","morning_report","data","guardrails","state_management","trade_plans",
  "deployment","notifications","integrations","reports_exports","risk_dashboards",
  "strategy_modules","system_evolution","security","intelligence","training",
  "research","portfolio_tools","future_proofing","collaboration","advanced_automations",
  "advanced_portfolio","ai_enhancements","expansion","resilience","monetization",
  "future_ai","long_term_scaling","edge_cases","meta","experimental"
]

path = os.environ.get("PREFS_PATH","config/vega_prefs.yaml")
with open(path,"r",encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}

missing = [k for k in REQUIRED_TOP if k not in cfg]
if missing:
    print("Missing top-level keys:", missing)
    sys.exit(1)

# sanity checks (just a few examples)
assert isinstance(cfg["morning_report"]["status_banner"], bool)
assert isinstance(cfg["github"]["weekly_module_drop"], bool)
assert cfg["notifications"]["slack_discord_alerts"] in (True, False)

print("vega_prefs.yaml OK")
