"""Cooldown policy: prevent a job from re-running too soon after a failure."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from cronwatch.log import get_log_dir


@dataclass
class CooldownPolicy:
    """Defines how long a job must wait after a failure before running again."""

    seconds: int = 0

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError("cooldown seconds must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.seconds > 0

    @classmethod
    def from_config(cls, cfg: Optional[Dict]) -> "CooldownPolicy":
        if not cfg:
            return cls()
        return cls(seconds=int(cfg.get("seconds", 0)))


def get_cooldown_state_path(job_name: str, log_dir: Optional[Path] = None) -> Path:
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / "cooldown" / f"{job_name}.json"


def load_cooldown_state(job_name: str, log_dir: Optional[Path] = None) -> Dict:
    path = get_cooldown_state_path(job_name, log_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_cooldown_state(job_name: str, state: Dict, log_dir: Optional[Path] = None) -> None:
    path = get_cooldown_state_path(job_name, log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def record_failure(job_name: str, log_dir: Optional[Path] = None) -> None:
    """Record the timestamp of the most recent failure for a job."""
    state = load_cooldown_state(job_name, log_dir)
    state["last_failure"] = time.time()
    save_cooldown_state(job_name, state, log_dir)


def clear_cooldown(job_name: str, log_dir: Optional[Path] = None) -> None:
    """Clear the cooldown state (e.g. after a successful run)."""
    state = load_cooldown_state(job_name, log_dir)
    state.pop("last_failure", None)
    save_cooldown_state(job_name, state, log_dir)


def is_cooling_down(job_name: str, policy: CooldownPolicy, log_dir: Optional[Path] = None) -> bool:
    """Return True if the job is still within its cooldown window."""
    if not policy.enabled:
        return False
    state = load_cooldown_state(job_name, log_dir)
    last_failure = state.get("last_failure")
    if last_failure is None:
        return False
    return (time.time() - last_failure) < policy.seconds
