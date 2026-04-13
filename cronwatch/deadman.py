"""Deadman switch support: alert when a job has NOT run within an expected window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from cronwatch.log import get_log_dir


@dataclass
class DeadmanPolicy:
    """Policy describing how long a job may be silent before raising an alert."""

    max_silence_seconds: int = 0  # 0 means disabled

    def __post_init__(self) -> None:
        if self.max_silence_seconds < 0:
            raise ValueError("max_silence_seconds must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.max_silence_seconds > 0

    @classmethod
    def from_config(cls, cfg: dict) -> "DeadmanPolicy":
        return cls(
            max_silence_seconds=int(cfg.get("max_silence_seconds", 0))
        )


def get_deadman_state_path(log_dir: Optional[Path] = None) -> Path:
    base = log_dir or get_log_dir()
    return base / "deadman_state.json"


def load_deadman_states(log_dir: Optional[Path] = None) -> Dict[str, float]:
    """Return mapping of job_name -> last_seen_timestamp (epoch seconds)."""
    path = get_deadman_state_path(log_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_deadman_states(states: Dict[str, float], log_dir: Optional[Path] = None) -> None:
    path = get_deadman_state_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(states, fh)


def record_job_seen(job_name: str, log_dir: Optional[Path] = None, ts: Optional[float] = None) -> None:
    """Record that *job_name* was observed running right now (or at *ts*)."""
    states = load_deadman_states(log_dir)
    states[job_name] = ts if ts is not None else time.time()
    save_deadman_states(states, log_dir)


def is_overdue(job_name: str, policy: DeadmanPolicy, log_dir: Optional[Path] = None) -> bool:
    """Return True when *job_name* has been silent longer than the policy allows."""
    if not policy.enabled:
        return False
    states = load_deadman_states(log_dir)
    last_seen = states.get(job_name)
    if last_seen is None:
        # Never seen — treat as overdue
        return True
    return (time.time() - last_seen) > policy.max_silence_seconds
