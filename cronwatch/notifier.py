"""Notification module for sending email and Slack alerts on cron job failures."""

import smtplib
import urllib.request
import urllib.error
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from cronwatch.config import CronwatchConfig
from cronwatch.runner import JobResult

logger = logging.getLogger(__name__)


def build_email_body(result: JobResult) -> str:
    """Build a human-readable email body from a JobResult."""
    lines = [
        f"Cron job FAILED: {result.command}",
        f"Exit code: {result.exit_code}",
        f"Duration: {result.duration:.2f}s",
        "",
    ]
    if result.stdout:
        lines += ["--- STDOUT ---", result.stdout, ""]
    if result.stderr:
        lines += ["--- STDERR ---", result.stderr, ""]
    return "\n".join(lines)


def send_email(result: JobResult, config: CronwatchConfig) -> bool:
    """Send an email alert. Returns True on success, False on failure."""
    ec = config.email
    if not ec or not ec.enabled:
        return False

    msg = MIMEMultipart()
    msg["From"] = ec.from_address
    msg["To"] = ", ".join(ec.to_addresses)
    msg["Subject"] = f"[cronwatch] Job failed: {result.command}"
    msg.attach(MIMEText(build_email_body(result), "plain"))

    try:
        with smtplib.SMTP(ec.smtp_host, ec.smtp_port) as server:
            if ec.use_tls:
                server.starttls()
            if ec.username and ec.password:
                server.login(ec.username, ec.password)
            server.sendmail(ec.from_address, ec.to_addresses, msg.as_string())
        logger.info("Email alert sent for job: %s", result.command)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email alert: %s", exc)
        return False


def send_slack(result: JobResult, config: CronwatchConfig) -> bool:
    """Send a Slack webhook alert. Returns True on success, False on failure."""
    sc = config.slack
    if not sc or not sc.enabled:
        return False

    payload = {
        "text": (
            f":x: *Cron job failed*: `{result.command}`\n"
            f"Exit code: `{result.exit_code}` | Duration: `{result.duration:.2f}s`"
        )
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        sc.webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
        logger.info("Slack alert sent for job: %s", result.command)
        return True
    except urllib.error.URLError as exc:
        logger.error("Failed to send Slack alert: %s", exc)
        return False


def notify(result: JobResult, config: CronwatchConfig) -> None:
    """Dispatch all configured notifications for a failed job."""
    if result.exit_code == 0:
        return
    send_email(result, config)
    send_slack(result, config)
