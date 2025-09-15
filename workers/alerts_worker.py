import os, sys, argparse, logging, datetime as dt
from email_client import EmailClient

LOG = logging.getLogger("alerts-worker")

REQUIRED_SECRETS = ["SENDGRID_API_KEY", "ALERTS_TO", "ALERTS_FROM"]

def require_env(keys):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {missing}")

def build_message(dry_run: bool) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "DRY-RUN" if dry_run else "LIVE"
    return (f"Vega Alerts Worker ({status})\n"
            f"Timestamp: {now}\n"
            f"Polygon Key: {'SET' if os.getenv('POLYGON_API_KEY') else 'MISSING'}\n"
            f"IBKR User: {'SET' if os.getenv('IBKR_USERNAME') else 'MISSING'}\n")

def run_scan() -> list[str]:
    """
    Placeholder: put your actual alert conditions here.
    Return a list of alert lines. Empty list = nothing to email.
    The key is: NEVER raise on 'no data' or 'no matches'.
    """
    alerts = []
    # Example condition (stub): if we had market data, append alerts.
    # Keep this tolerant: all failures should be logged, not crash the job.
    return alerts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Send a test email and exit")
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL","INFO"))
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    try:
        require_env(REQUIRED_SECRETS)
        client = EmailClient(
            api_key=os.environ["SENDGRID_API_KEY"],
            from_addr=os.environ["ALERTS_FROM"],
            to_addr=os.environ["ALERTS_TO"]
        )
    except Exception as e:
        LOG.exception("Startup/env validation failed")
        sys.exit(2)

    if args.dry_run:
        subject = "Vega Alerts Worker: DRY-RUN OK"
        body = build_message(dry_run=True)
        try:
            client.send(subject, body)
            LOG.info("Dry-run email sent.")
            return 0
        except Exception:
            LOG.exception("Dry-run email failed")
            return 2

    # Live path
    try:
        alerts = run_scan()
    except Exception:
        LOG.exception("Scan crashed")
        # Still tell you it crashed, but via email so you see details immediately.
        client.send("Vega Alerts Worker: scan crashed",
                    "See Actions logs for traceback.")
        return 1

    if not alerts:
        LOG.info("No alerts today. Exiting gracefully.")
        # Optional: send a heartbeat email once per day; skip to avoid noise.
        return 0

    # Email the compiled alerts
    subject = f"Vega Alerts ({len(alerts)})"
    body = "\n".join(alerts)
    try:
        client.send(subject, body)
        LOG.info("Alerts email sent.")
        return 0
    except Exception:
        LOG.exception("Failed to send alerts email")
        return 1

if __name__ == "__main__":
    sys.exit(main())
