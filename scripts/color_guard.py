#!/usr/bin/env python3
import os, json, pathlib, datetime as dt
region = os.getenv("REGION","NA")
outdir = pathlib.Path("alerts"); outdir.mkdir(parents=True, exist_ok=True)
out = outdir / f"color_guard_{'europe' if region=='EU' else region.lower()}.json"
payload = {"region": region, "status": "ok", "generated_at_utc": dt.datetime.utcnow().isoformat(timespec="seconds")+"Z", "note": "Generic fallback"}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"[color_guard_fallback] wrote {out}")
