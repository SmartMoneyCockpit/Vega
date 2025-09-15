import os, json, textwrap
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def badge(res):
    return "✅ SUCCESS" if res == "success" else ("❌ FAILURE" if res == "failure" else f"⚠️ {res.upper()}")

def main():
    ctx = json.loads(os.environ.get("GITHUB_CONTEXT","{}"))
    repo   = ctx.get("repository","")
    run_id = ctx.get("run_id","")
    sha    = ctx.get("sha","")[:7]
    ref    = ctx.get("ref","")
    actor  = ctx.get("actor","")
    event  = ctx.get("event_name","")
    url    = f"https://github.com/{repo}/actions/runs/{run_id}"

    job_lint  = os.getenv("JOB_LINT","unknown")
    job_build = os.getenv("JOB_BUILD","unknown")

    subject = f"[{repo}] CI {badge('success' if job_lint=='success' and job_build=='success' else 'failure')} — {sha} ({event})"
    body = textwrap.dedent(f"""
    Repository: {repo}
    Ref:        {ref}
    Commit:     {sha}
    Actor:      {actor}
    Event:      {event}

    Job Results:
      • Lint : {badge(job_lint)}
      • Build: {badge(job_build)}

    Run URL:
      {url}
    """).strip()

    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    msg = Mail(
        from_email=os.environ["ALERTS_FROM"],
        to_emails=os.environ["ALERTS_TO"],
        subject=subject,
        plain_text_content=body
    )
    sg.send(msg)

if __name__ == "__main__":
    main()
