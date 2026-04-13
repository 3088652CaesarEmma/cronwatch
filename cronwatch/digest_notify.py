"""Send digest summary notifications via email and/or Slack."""

from __future__ import annotations

from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.digest import DigestPolicy, build_digest, is_digest_due, mark_digest_sent
from cronwatch.log import get_log_dir
from cronwatch.notifier import send_email, send_slack
from cronwatch.summary import RunSummary


def _format_digest_email(summary: RunSummary) -> str:
    lines = [
        "Cronwatch Digest Report",
        "=" * 30,
        f"Total jobs run : {summary.total}",
        f"Succeeded      : {summary.succeeded}",
        f"Failed         : {summary.failed}",
        "",
    ]
    for result in summary.results:
        status = "OK" if result.exit_code == 0 else "FAIL"
        lines.append(f"  [{status}] {result.command}")
    return "\n".join(lines)


def _format_digest_slack(summary: RunSummary) -> str:
    emoji = ":white_check_mark:" if summary.failed == 0 else ":x:"
    return (
        f"{emoji} *Cronwatch Digest* — "
        f"{summary.succeeded}/{summary.total} succeeded, "
        f"{summary.failed} failed."
    )


def send_digest(
    config: CronwatchConfig,
    job_names: List[str],
    policy: DigestPolicy,
    log_dir: str | None = None,
) -> bool:
    """Build and send a digest if due. Returns True if digest was sent."""
    if log_dir is None:
        log_dir = get_log_dir(config)

    if not is_digest_due(policy, log_dir):
        return False

    summary = build_digest(job_names, log_dir, policy)
    if summary is None:
        return False

    body = _format_digest_email(summary)
    slack_text = _format_digest_slack(summary)

    if config.email and config.email.enabled:
        send_email(config.email, subject="Cronwatch Digest", body=body)

    if config.slack and config.slack.enabled:
        send_slack(config.slack, message=slack_text)

    mark_digest_sent(log_dir)
    return True
