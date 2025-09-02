
import os, smtplib, ssl
from email.mime.text import MIMEText

def _get_env(name: str, *alts):
    for n in (name, *alts):
        v = os.getenv(n)
        if v:
            return v
    return None

def send_mail(subject: str, body: str) -> None:
    # Compatibility across different env naming conventions
    host = _get_env("SMTP_HOST", "VEGA_EMAIL_HOST", "EMAIL_HOST")
    port = int(_get_env("SMTP_PORT", "VEGA_EMAIL_PORT", "EMAIL_PORT") or "587")
    user = _get_env("SMTP_USER", "VEGA_EMAIL_USER", "EMAIL_USER")
    password = _get_env("SMTP_PASS", "VEGA_EMAIL_PASS", "EMAIL_PASS")
    sender = _get_env("SMTP_FROM", "EMAIL_FROM") or user
    to      = _get_env("SMTP_TO", "EMAIL_TO", "VEGA_EMAIL_TO")

    missing = [k for k,v in {
        "SMTP_HOST":host, "SMTP_PORT":port, "SMTP_USER":user,
        "SMTP_PASS":password, "SMTP_FROM":sender, "SMTP_TO":to
    }.items() if not v]
    if missing:
        raise RuntimeError("Email disabled — missing: " + ", ".join(missing) +
                           ". Set these in your environment (.env) or disable email in settings.")

    msg = MIMEText(body or "", "plain", "utf-8")
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = sender
    msg["To"] = to

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=20) as s:
            try:
                s.starttls(context=ctx)
            except smtplib.SMTPException:
                pass  # if server already TLS
            s.login(user, password)
            s.sendmail(sender, [to], msg.as_string())
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError("Email auth failed — check SMTP_USER/SMTP_PASS.") from e
    except smtplib.SMTPConnectError as e:
        raise RuntimeError("Email connection failed — check SMTP_HOST/PORT and network.") from e
    except Exception as e:
        raise RuntimeError(f"Email send failed: {e}") from e
