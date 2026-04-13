"""Rate limiting for notifications to avoid alert fatigue."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from cronwatch.log import get_log_dir


_STATE_FILENAME = "ratelimit_state.json"


@dataclass
class RateLimitPolicy:
    """Policy controlling how often notifications can be sent per job."""

    min_interval_seconds: int = 3600  # default: at most once per hour

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")

    @classmethod
    def from_config(cls, cfg: dict) -> "RateLimitPolicy":
        return cls(
            min_interval_seconds=int(
                cfg.get("min_interval_seconds", 3600)
            )
        )

    @property
    def enabled(self) -> bool:
        return self.min_interval_seconds > 0


def get_ratelimit_state_path(log_dir: Optional[Path] = None) -> Path:
    base = log_dir or get_log_dir()
    return base / _STATE_FILENAME


def load_ratelimit_state(log_dir: Optional[Path] = None) -> Dict[str, float]:
    """Return mapping of job_name -> last_notified_timestamp."""
    path = get_ratelimit_state_path(log_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_ratelimit_state(
    state: Dict[str, float], log_dir: Optional[Path] = None
) -> None:
    path = get_ratelimit_state_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def is_rate_limited(
    job_name: str,
    policy: RateLimitPolicy,
    log_dir: Optional[Path] = None,
    _now: Optional[float] = None,
) -> bool:
    """Return True if a notification for *job_name* should be suppressed."""
    if not policy.enabled:
        return False
    state = load_ratelimit_state(log_dir)
    last = state.get(job_name)
    if last is None:
        return False
    now = _now if _now is not None else time.time()
    return (now - last) < policy.min_interval_seconds


def record_notification(
    job_name: str,
    log_dir: Optional[Path] = None,
    _now: Optional[float] = None,
) -> None:
    """Persist the current timestamp as the last notification time for *job_name*."""
    state = load_ratelimit_state(log_dir)
    state[job_name] = _now if _now is not None else time.time()
    save_ratelimit_state(state, log_dir)
