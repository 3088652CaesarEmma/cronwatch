"""Runtime budget enforcement — limits how long a job may run within a time window."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from cronwatch.log import get_log_dir


@dataclass
class BudgetPolicy:
    """Defines a maximum cumulative runtime (seconds) allowed within a rolling window."""

    max_seconds: float = 0.0          # 0 means disabled
    window_seconds: float = 3600.0    # rolling window length in seconds

    def __post_init__(self) -> None:
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    @property
    def enabled(self) -> bool:
        return self.max_seconds > 0

    @classmethod
    def from_config(cls, cfg: Optional[Dict]) -> "BudgetPolicy":
        if not cfg:
            return cls()
        return cls(
            max_seconds=float(cfg.get("max_seconds", 0.0)),
            window_seconds=float(cfg.get("window_seconds", 3600.0)),
        )


def get_budget_state_path(job_name: str) -> Path:
    return get_log_dir() / "budget" / f"{job_name}.json"


def _load_runs(path: Path, window_seconds: float) -> List[float]:
    """Load run durations recorded within the current window."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        cutoff = time.time() - window_seconds
        return [r["duration"] for r in data.get("runs", []) if r.get("ts", 0) >= cutoff]
    except (json.JSONDecodeError, KeyError):
        return []


def _save_runs(path: Path, runs: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"runs": runs}, indent=2))


def record_run(job_name: str, duration: float) -> None:
    """Append a completed run duration to the budget state."""
    path = get_budget_state_path(job_name)
    try:
        existing = json.loads(path.read_text()).get("runs", []) if path.exists() else []
    except (json.JSONDecodeError, ValueError):
        existing = []
    existing.append({"ts": time.time(), "duration": duration})
    _save_runs(path, existing)


def budget_used(job_name: str, policy: BudgetPolicy) -> float:
    """Return total seconds used within the current window."""
    path = get_budget_state_path(job_name)
    runs = _load_runs(path, policy.window_seconds)
    return sum(runs)


def check_budget(job_name: str, policy: BudgetPolicy) -> bool:
    """Return True if the job is still within its budget, False if exceeded."""
    if not policy.enabled:
        return True
    return budget_used(job_name, policy) < policy.max_seconds
