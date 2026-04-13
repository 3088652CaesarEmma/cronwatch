"""Quota policy: limit the number of times a job may run within a time window."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class QuotaPolicy:
    max_runs: int = 0          # 0 means disabled
    window_seconds: int = 3600 # default: 1-hour rolling window

    def __post_init__(self) -> None:
        if self.max_runs < 0:
            raise ValueError("max_runs must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    @property
    def enabled(self) -> bool:
        return self.max_runs > 0

    @classmethod
    def from_config(cls, cfg: dict | None) -> "QuotaPolicy":
        if not cfg:
            return cls()
        return cls(
            max_runs=int(cfg.get("max_runs", 0)),
            window_seconds=int(cfg.get("window_seconds", 3600)),
        )


def get_quota_state_path(log_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(log_dir) / "quota" / f"{safe}.json"


def _load_timestamps(path: Path) -> List[float]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [float(t) for t in data.get("runs", [])]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def _save_timestamps(path: Path, timestamps: List[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"runs": timestamps}))


def check_quota(policy: QuotaPolicy, log_dir: str, job_name: str) -> bool:
    """Return True if the job is allowed to run (quota not exceeded)."""
    if not policy.enabled:
        return True
    path = get_quota_state_path(log_dir, job_name)
    now = time.time()
    cutoff = now - policy.window_seconds
    timestamps = [t for t in _load_timestamps(path) if t >= cutoff]
    return len(timestamps) < policy.max_runs


def record_quota_run(policy: QuotaPolicy, log_dir: str, job_name: str) -> None:
    """Record that a job has just run (for quota tracking)."""
    if not policy.enabled:
        return
    path = get_quota_state_path(log_dir, job_name)
    now = time.time()
    cutoff = now - policy.window_seconds
    timestamps = [t for t in _load_timestamps(path) if t >= cutoff]
    timestamps.append(now)
    _save_timestamps(path, timestamps)
