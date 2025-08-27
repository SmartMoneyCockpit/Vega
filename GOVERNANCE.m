# Vega Governance Guide

This cockpit uses a **single source of truth** at `config/vega_prefs.yaml`. Changes follow:
- **semver** in `config/version.json` (`major.minor.patch`)
- All changes logged in `CHANGELOG.md`
- GitHub Actions auto-bump version on edits to `config/vega_prefs.yaml`

**Rules**
1. `vega_prefs.yaml` is **law**. Code reads flags; do not hardcode.
2. Prefer flipping booleans in prefs over editing workflows.
3. “Kill switches” live under `control:` (if added) and are honored by all modules.

**Change Types**
- Patch: typo/description or off-by-one thresholds (no behavior shift)
- Minor: enable/disable existing features/modules
- Major: add/remove categories; change philosophy (meta/autonomy), or defaults

**Process**
- Open PR with changes to `config/vega_prefs.yaml`
- Action `prefs_validator.yaml` runs
- On merge to `main`, `prefs_versioning.yaml` bumps version and appends CHANGELOG
