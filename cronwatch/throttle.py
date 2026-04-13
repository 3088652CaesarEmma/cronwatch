"""Throttle policy: limits how often notifications are sent for a given job."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from cronwatch.log import get_log_dir

_THROTTLE_STATE_FILE = "throttle_state.json"


@dataclass
class ThrottlePolicy:
    """Controls minimum seconds between repeated notifications for a job."""

    min_interval: int = 0  # 0 means disabled

    def __post_init__(self) -> None:
        if self.min_interval < 0:
            raise ValueError("min_interval must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.min_interval > 0

    @classmethod
    def from_config(cls, cfg: Optional[Dict]) -> "ThrottlePolicy":
        if not cfg:
            return cls()
        return cls(min_interval=int(cfg.get("min_interval", 0)))


def get_throttle_state_path(log_dir: Optional[Path] = None) -> Path:
    base = log_dir or get_log_dir()
    return base / _THROTTLE_STATE_FILE


def load_throttle_state(log_dir: Optional[Path] = None) -> Dict[str, float]:
    path = get_throttle_state_path(log_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_throttle_state(state: Dict[str, float], log_dir: Optional[Path] = None) -> None:
    path = get_throttle_state_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def should_throttle(job_name: str, policy: ThrottlePolicy, log_dir: Optional[Path] = None) -> bool:
    """Return True if the notification for job_name should be suppressed."""
    if not policy.enabled:
        return False
    state = load_throttle_state(log_dir)
    last_sent = state.get(job_name)
    if last_sent is None:
        return False
    return (time.time() - last_sent) < policy.min_interval


def record_notification(job_name: str, log_dir: Optional[Path] = None) -> None:
    """Record that a notification was sent for job_name right now."""
    state = load_throttle_state(log_dir)
    state[job_name] = time.time()
    save_throttle_state(state, log_dir)
