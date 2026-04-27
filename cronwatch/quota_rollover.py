"""Quota rollover policy: automatically reset quota counts on a calendar schedule."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir

_VALID_PERIODS = {"hourly", "daily", "weekly", "monthly"}


@dataclass
class QuotaRolloverPolicy:
    period: Optional[str] = None  # hourly | daily | weekly | monthly

    def __post_init__(self) -> None:
        if self.period is not None:
            if not isinstance(self.period, str):
                raise TypeError("period must be a string")
            self.period = self.period.strip().lower()
            if self.period not in _VALID_PERIODS:
                raise ValueError(f"period must be one of {sorted(_VALID_PERIODS)}")

    @property
    def enabled(self) -> bool:
        return self.period is not None

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "QuotaRolloverPolicy":
        if not cfg:
            return cls()
        return cls(period=cfg.get("period"))


def get_rollover_state_path(job_name: str, log_dir: Optional[Path] = None) -> Path:
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / "rollover" / f"{job_name}.json"


def load_rollover_state(job_name: str, log_dir: Optional[Path] = None) -> dict:
    path = get_rollover_state_path(job_name, log_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_rollover_state(job_name: str, state: dict, log_dir: Optional[Path] = None) -> None:
    path = get_rollover_state_path(job_name, log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(state, fh)


def _period_bucket(period: str) -> str:
    """Return a string key representing the current rollover bucket."""
    t = time.gmtime()
    if period == "hourly":
        return f"{t.tm_year}-{t.tm_yday:03d}-{t.tm_hour:02d}"
    if period == "daily":
        return f"{t.tm_year}-{t.tm_yday:03d}"
    if period == "weekly":
        return f"{t.tm_year}-W{t.tm_yday // 7:02d}"
    # monthly
    return f"{t.tm_year}-{t.tm_mon:02d}"


def maybe_rollover(job_name: str, policy: QuotaRolloverPolicy, log_dir: Optional[Path] = None) -> bool:
    """Return True and clear state if a rollover occurred, else False."""
    if not policy.enabled:
        return False
    bucket = _period_bucket(policy.period)  # type: ignore[arg-type]
    state = load_rollover_state(job_name, log_dir)
    if state.get("bucket") != bucket:
        save_rollover_state(job_name, {"bucket": bucket}, log_dir)
        return True
    return False
