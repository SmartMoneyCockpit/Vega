
# Vega Accordion+Search — Massive Delta (Non-Destructive)

## New Files
- `menu_config.yaml` — optional fixed menu (edit later)
- `core/menu_config.py` — load fixed menu YAML
- `core/search.py` — fuzzy search support
- `core/breadcrumbs.py` — breadcrumb helper
- `core/nav_adv.py` — accordion + search + recents + icons
- `core/autoreg.py` — auto-discovery of `pages/**`
- `core/registry.py` — route registry decorator
- `app_menu_refactor_advanced.py` — entrypoint using all the above
- `pages/all_pages.py` — optional utility page that lists every registered page

## Use It (no overwrites)
1. Copy the **new files** into your repo root (beside your existing app).
2. Test locally:
   ```bash
   streamlit run app_menu_refactor_advanced.py
   ```
   Or set Render Start Command to the same.
3. (Optional) Edit `menu_config.yaml` to pin a fixed menu. Leave it empty to auto-discover.

## Notes
- Deep links: `?page=<route>`
- Recently used list remembers your 8 most recent page routes (per session)
- Safe rollback: delete added files to revert.
