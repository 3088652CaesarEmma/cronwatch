"""Track consecutive success/failure streaks for cron jobs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from cronwatch.log import get_log_dir
from cronwatch.runner import JobResult


def get_streak_path(log_dir: str) -> Path:
    return Path(log_dir) / "streaks.json"


@dataclass
class StreakState:
    job_name: str
    current: int = 0          # positive = consecutive successes, negative = consecutive failures
    best_success: int = 0
    worst_failure: int = 0    # stored as positive integer

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "current": self.current,
            "best_success": self.best_success,
            "worst_failure": self.worst_failure,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StreakState":
        return cls(
            job_name=d["job_name"],
            current=d.get("current", 0),
            best_success=d.get("best_success", 0),
            worst_failure=d.get("worst_failure", 0),
        )


def load_streaks(log_dir: str) -> Dict[str, StreakState]:
    path = get_streak_path(log_dir)
    if not path.exists():
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {k: StreakState.from_dict(v) for k, v in raw.items()}


def save_streaks(log_dir: str, states: Dict[str, StreakState]) -> None:
    path = get_streak_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({k: v.to_dict() for k, v in states.items()}, f, indent=2)


def record_streak(result: JobResult, log_dir: Optional[str] = None) -> StreakState:
    """Update and persist the streak for the job in *result*."""
    if log_dir is None:
        log_dir = get_log_dir()
    states = load_streaks(log_dir)
    name = result.command
    state = states.get(name, StreakState(job_name=name))

    if result.exit_code == 0:
        state.current = max(state.current, 0) + 1
        state.best_success = max(state.best_success, state.current)
    else:
        state.current = min(state.current, 0) - 1
        state.worst_failure = max(state.worst_failure, abs(state.current))

    states[name] = state
    save_streaks(log_dir, states)
    return state


def get_streak(job_name: str, log_dir: Optional[str] = None) -> Optional[StreakState]:
    if log_dir is None:
        log_dir = get_log_dir()
    return load_streaks(log_dir).get(job_name)
