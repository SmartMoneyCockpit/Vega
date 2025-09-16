"""
A+ Digest Email module (stub). Real deployment uses SendGrid via env vars.
"""
import os
def build_digest(setups):
    # setups: list of dicts {ticker, entry, stop, targets, rr, reason}
    lines = [f"- {s['ticker']}: entry {s['entry']} stop {s['stop']} R/R {s['rr']}" for s in setups]
    return "\n".join(lines) if lines else "No A+ setups today."
