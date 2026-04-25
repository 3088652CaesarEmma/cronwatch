"""Quota reset policy — allows scheduled or manual reset of quota counters."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


@dataclass
class QuotaResetPolicy:
    """Policy controlling automatic quota counter resets."""

    reset_after: int = 0          # seconds; 0 = disabled
    reset_on_success: bool = False

    def __post_init__(self) -> None:
        if self.reset_after < 0:
            raise ValueError("reset_after must be >= 0")
        if not isinstance(self.reset_on_success, bool):
            raise TypeError("reset_on_success must be a bool")

    @property
    def enabled(self) -> bool:
        return self.reset_after > 0 or self.reset_on_success

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "QuotaResetPolicy":
        if not cfg:
            return cls()
        return cls(
            reset_after=int(cfg.get("reset_after", 0)),
            reset_on_success=bool(cfg.get("reset_on_success", False)),
        )


def get_quota_reset_state_path(job_name: str, log_dir: Optional[Path] = None) -> Path:
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / f"{job_name}.quota_reset.json"


def load_quota_reset_state(job_name: str, log_dir: Optional[Path] = None) -> dict:
    path = get_quota_reset_state_path(job_name, log_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_quota_reset_state(job_name: str, state: dict, log_dir: Optional[Path] = None) -> None:
    path = get_quota_reset_state_path(job_name, log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(state, fh)


def should_reset(policy: QuotaResetPolicy, job_name: str, success: bool,
                 log_dir: Optional[Path] = None) -> bool:
    """Return True if the quota counter for *job_name* should be reset now."""
    if not policy.enabled:
        return False
    if policy.reset_on_success and success:
        return True
    if policy.reset_after > 0:
        state = load_quota_reset_state(job_name, log_dir)
        last = state.get("last_reset", 0)
        if (time.time() - last) >= policy.reset_after:
            return True
    return False


def record_reset(job_name: str, log_dir: Optional[Path] = None) -> None:
    """Persist the timestamp of the most recent quota reset."""
    state = load_quota_reset_state(job_name, log_dir)
    state["last_reset"] = time.time()
    save_quota_reset_state(job_name, state, log_dir)
