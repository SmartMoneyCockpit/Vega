#!/usr/bin/env python3
import json, pathlib, datetime as dt
out = pathlib.Path("alerts")/ "color_guard_na.json"
out.parent.mkdir(parents=True, exist_ok=True)
payload = {
  "region": "NA",
  "status": "ok",
  "generated_at_utc": dt.datetime.utcnow().isoformat(timespec="seconds")+"Z",
  "note": "Placeholder Color Guard (NA)"
}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"[color_guard_na] wrote {out}")
