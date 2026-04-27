"""Quota alert policy: notify when quota usage exceeds a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwatch.quota import QuotaPolicy, get_quota_state_path, load_quota_state


@dataclass
class QuotaAlertPolicy:
    """Fire an alert when quota usage reaches a percentage threshold."""

    threshold: float = 0.0  # 0.0 means disabled
    notify_once: bool = True  # only alert once per window

    def __post_init__(self) -> None:
        if not isinstance(self.threshold, (int, float)):
            raise TypeError("threshold must be a number")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        if not isinstance(self.notify_once, bool):
            raise TypeError("notify_once must be a bool")

    @property
    def enabled(self) -> bool:
        return self.threshold > 0.0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "QuotaAlertPolicy":
        if not cfg:
            return cls()
        return cls(
            threshold=float(cfg.get("threshold", 0.0)),
            notify_once=bool(cfg.get("notify_once", True)),
        )


def check_quota_alert(
    job_name: str,
    quota_policy: QuotaPolicy,
    alert_policy: QuotaAlertPolicy,
    log_dir: str,
) -> Optional[str]:
    """Return a warning message if quota usage exceeds the alert threshold.

    Returns None when no alert should be raised.
    """
    if not alert_policy.enabled or not quota_policy.enabled:
        return None

    state_path = get_quota_state_path(job_name, log_dir)
    runs = load_quota_state(state_path, quota_policy.window_seconds)
    used = len(runs)
    limit = quota_policy.max_runs

    if limit <= 0:
        return None

    ratio = used / limit
    if ratio >= alert_policy.threshold:
        pct = int(ratio * 100)
        return (
            f"[quota-alert] {job_name}: {used}/{limit} runs used "
            f"({pct}% of quota, threshold={int(alert_policy.threshold * 100)}%)"
        )
    return None
