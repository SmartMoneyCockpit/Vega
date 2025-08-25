# Alerts YAML schema
- Files live in `config/alerts/*.yaml`
- We keep at most one or two *live* autos; everything else lives here.

## Keys
- `region`: APAC | NA | EU...
- `as_of`: YYYY-MM-DD
- `policy.keep_active_automations`: list of rules we keep as live autos (rare)
- `watchlist[]`:
  - `ticker`: e.g., SPY, 3697.T
  - `status`: short note for the cockpit card
  - `alerts[]`: one of
    - intraday_at_or_below / intraday_at_or_above
    - close_below / close_above / close_at_or_above
    - percent_move_from_close / percent_gain_from_open / percent_drawdown_from_open
    - ma_cross_up / ma_cross_down (with `ma:` 20/50 etc.)
  - `plan.entries[]` and `plan.targets[]`: free text for playbook
- `notes[]`: any session notes
