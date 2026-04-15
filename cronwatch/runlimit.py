"""Run limit policy: cap the maximum number of concurrent or sequential runs
allowed within a rolling time window, per job name."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class RunLimitPolicy:
    """Defines a maximum number of allowed runs in a given window (seconds)."""

    max_runs: int = 0          # 0 means disabled
    window_seconds: int = 3600 # rolling window, default 1 hour

    def __post_init__(self) -> None:
        if self.max_runs < 0:
            raise ValueError("max_runs must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    @property
    def enabled(self) -> bool:
        return self.max_runs > 0

    @classmethod
    def from_config(cls, cfg: dict | None) -> "RunLimitPolicy":
        if not cfg:
            return cls()
        return cls(
            max_runs=int(cfg.get("max_runs", 0)),
            window_seconds=int(cfg.get("window_seconds", 3600)),
        )


def get_runlimit_state_path(log_dir: str, job_name: str) -> str:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    state_dir = os.path.join(log_dir, "runlimit")
    os.makedirs(state_dir, exist_ok=True)
    return os.path.join(state_dir, f"{safe}.json")


def _load_timestamps(path: str, window_seconds: int) -> List[float]:
    """Load run timestamps, pruning entries outside the rolling window."""
    now = time.time()
    cutoff = now - window_seconds
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        data = json.load(fh)
    return [ts for ts in data.get("timestamps", []) if ts >= cutoff]


def _save_timestamps(path: str, timestamps: List[float]) -> None:
    with open(path, "w") as fh:
        json.dump({"timestamps": timestamps}, fh)


def check_run_limit(policy: RunLimitPolicy, log_dir: str, job_name: str) -> bool:
    """Return True if the job is allowed to run (under the limit)."""
    if not policy.enabled:
        return True
    path = get_runlimit_state_path(log_dir, job_name)
    timestamps = _load_timestamps(path, policy.window_seconds)
    return len(timestamps) < policy.max_runs


def record_run(policy: RunLimitPolicy, log_dir: str, job_name: str) -> None:
    """Record a new run timestamp for the job."""
    if not policy.enabled:
        return
    path = get_runlimit_state_path(log_dir, job_name)
    timestamps = _load_timestamps(path, policy.window_seconds)
    timestamps.append(time.time())
    _save_timestamps(path, timestamps)
