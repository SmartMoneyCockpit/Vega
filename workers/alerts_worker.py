# --- at top of file ---
import os, sys, json, traceback
from dataclasses import dataclass

class KnownEmptyResult(Exception): ...
class ConfigError(Exception): ...

# call this where you build alerts
def write_artifact(alerts, path="alerts.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"count": len(alerts), "alerts": alerts}, f, ensure_ascii=False, indent=2)

def main():
    # 1) sanity-check required config, fail fast with helpful message
    required = ["SENDGRID_API_KEY","ALERTS_TO","ALERTS_FROM","POLYGON_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ConfigError(f"Missing required secrets: {', '.join(missing)}")

    # 2) your current scan logic -> returns a list
    alerts = run_scan()  # <-- your existing function

    # 3) expected state: zero alerts => SUCCESS (exit 0) but upload artifact
    if not alerts:
        write_artifact(alerts)
        print("No alerts today; exiting 0.")
        return

    # 4) send alerts; if sending fails, let it raise -> exit 1 below
    send_alerts(alerts)
    write_artifact(alerts)
    print(f"Sent {len(alerts)} alerts.")

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KnownEmptyResult:
        # Treat as success; artifact should already be written if needed
        sys.exit(0)
    except ConfigError as e:
        # Clear, actionable failure (keeps CI red with a helpful message)
        print(f"[CONFIG ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
