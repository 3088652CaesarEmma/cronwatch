"""Pin policy: lock a job to a specific cron schedule version.

Allows operators to 'pin' a job so it only runs if its schedule
matches an expected value, preventing accidental execution after
a config change.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


class PinViolationError(Exception):
    def __init__(self, job_name: str, expected: str, actual: str) -> None:
        self.job_name = job_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Job '{job_name}' schedule pin violated: "
            f"expected '{expected}', got '{actual}'"
        )


@dataclass
class PinPolicy:
    schedule: Optional[str] = None

    def __post_init__(self) -> None:
        if self.schedule is not None:
            if not isinstance(self.schedule, str):
                raise TypeError("schedule must be a string or None")
            self.schedule = self.schedule.strip() or None

    @property
    def enabled(self) -> bool:
        return self.schedule is not None

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "PinPolicy":
        if not cfg:
            return cls()
        return cls(schedule=cfg.get("schedule"))

    def check(self, job_name: str, actual_schedule: str) -> None:
        """Raise PinViolationError if actual schedule doesn't match pin."""
        if not self.enabled:
            return
        if actual_schedule.strip() != self.schedule:
            raise PinViolationError(job_name, self.schedule, actual_schedule)


def get_pin_state_path(log_dir: str) -> str:
    return os.path.join(log_dir, "pin_state.json")


def load_pin_states(log_dir: str) -> dict:
    path = get_pin_state_path(log_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def save_pin_states(log_dir: str, states: dict) -> None:
    path = get_pin_state_path(log_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(states, fh)


def record_pin(log_dir: str, job_name: str, schedule: str) -> None:
    """Persist the pinned schedule for a job."""
    states = load_pin_states(log_dir)
    states[job_name] = schedule
    save_pin_states(log_dir, states)


def get_pinned_schedule(log_dir: str, job_name: str) -> Optional[str]:
    states = load_pin_states(log_dir)
    return states.get(job_name)
