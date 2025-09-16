def build_digest(setups):
    lines = [f"- {s['ticker']}: entry {s['entry']} stop {s['stop']} R/R {s['rr']} — {s.get('reason','')}" for s in setups]
    return "\n".join(lines) if lines else "No A+ setups today."
