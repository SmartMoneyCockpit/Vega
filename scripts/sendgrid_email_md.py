#!/usr/bin/env python3
"""
Send a Markdown file via SendGrid as HTML <pre>…</pre>.
Usage:
  python scripts/sendgrid_email_md.py --api-key $SENDGRID_API_KEY \
      --to you@example.com --from reports@vega.local \
      --subject "Morning Report" --file artifacts/morning_report/file.md
"""
import argparse, html, json, os, sys, requests

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api-key", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--from", dest="sender", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--file", required=True)
    args = p.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(0)  # do not fail the job

    body = "<pre>" + html.escape(open(args.file, "r", encoding="utf-8").read()) + "</pre>"
    payload = {
        "personalizations": [{"to": [{"email": args.to}]}],
        "from": {"email": args.sender},
        "subject": args.subject,
        "content": [{"type": "text/html", "value": body}],
    }
    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {args.api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=20,
    )
    if r.status_code // 100 != 2:
        print(f"SendGrid error: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
