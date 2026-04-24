"""Escalation policy for cronwatch.

Supports notifying additional recipients or channels when a job has been
failing repeatedly beyond a configurable threshold.  Escalation state is
persisted alongside other job state so it survives process restarts.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from cronwatch.log import get_log_dir


@dataclass
class EscalationPolicy:
    """Configuration for failure escalation.

    Attributes:
        threshold: Number of consecutive failures before escalating.
        emails: Additional email addresses to notify on escalation.
        slack_channels: Additional Slack channels to notify on escalation.
        reset_on_success: Whether to reset the escalation counter after a
            successful run.
    """

    threshold: int = 0
    emails: List[str] = field(default_factory=list)
    slack_channels: List[str] = field(default_factory=list)
    reset_on_success: bool = True

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("threshold must be >= 0")
        if not isinstance(self.emails, list):
            raise TypeError("emails must be a list")
        if not isinstance(self.slack_channels, list):
            raise TypeError("slack_channels must be a list")

    @property
    def enabled(self) -> bool:
        """Return True when escalation is configured."""
        return self.threshold > 0 and (
            bool(self.emails) or bool(self.slack_channels)
        )

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "EscalationPolicy":
        """Build an EscalationPolicy from a raw config dict (or None)."""
        if not cfg:
            return cls()
        return cls(
            threshold=int(cfg.get("threshold", 0)),
            emails=list(cfg.get("emails") or []),
            slack_channels=list(cfg.get("slack_channels") or []),
            reset_on_success=bool(cfg.get("reset_on_success", True)),
        )


# ---------------------------------------------------------------------------
# Persistent state helpers
# ---------------------------------------------------------------------------

def get_escalation_state_path(job_name: str, log_dir: Optional[str] = None) -> Path:
    """Return the path to the escalation state file for *job_name*."""
    base = Path(log_dir) if log_dir else get_log_dir()
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return base / f"{safe}.escalation.json"


def load_escalation_state(job_name: str, log_dir: Optional[str] = None) -> Dict:
    """Load persisted escalation state for *job_name*.

    Returns a dict with at least ``consecutive_failures`` (int) and
    ``escalated_at`` (float or None).
    """
    path = get_escalation_state_path(job_name, log_dir)
    if not path.exists():
        return {"consecutive_failures": 0, "escalated_at": None}
    try:
        with path.open() as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"consecutive_failures": 0, "escalated_at": None}


def save_escalation_state(job_name: str, state: Dict, log_dir: Optional[str] = None) -> None:
    """Persist escalation *state* for *job_name*."""
    path = get_escalation_state_path(job_name, log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(state, fh)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_failure(
    job_name: str,
    policy: EscalationPolicy,
    log_dir: Optional[str] = None,
) -> bool:
    """Record a failure for *job_name* and return True if escalation should fire.

    The escalation counter is incremented and persisted.  Returns ``True``
    when the consecutive failure count has just reached (or exceeded) the
    configured threshold for the first time in this escalation cycle.
    """
    if not policy.enabled:
        return False

    state = load_escalation_state(job_name, log_dir)
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

    should_fire = (
        state["consecutive_failures"] >= policy.threshold
        and state.get("escalated_at") is None
    )
    if should_fire:
        state["escalated_at"] = time.time()

    save_escalation_state(job_name, state, log_dir)
    return should_fire


def record_success(
    job_name: str,
    policy: EscalationPolicy,
    log_dir: Optional[str] = None,
) -> None:
    """Reset escalation state for *job_name* after a successful run."""
    if not policy.reset_on_success:
        return
    state = {"consecutive_failures": 0, "escalated_at": None}
    save_escalation_state(job_name, state, log_dir)
