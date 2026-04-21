"""Circuit breaker policy: skip job execution after N consecutive failures."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CircuitBreakerPolicy:
    """Configuration for the circuit breaker."""

    threshold: int = 0          # number of consecutive failures before opening; 0 = disabled
    reset_after: int = 300      # seconds before attempting to close the circuit

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("threshold must be >= 0")
        if self.reset_after <= 0:
            raise ValueError("reset_after must be > 0")

    @property
    def enabled(self) -> bool:
        return self.threshold > 0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "CircuitBreakerPolicy":
        if not cfg:
            return cls()
        return cls(
            threshold=int(cfg.get("threshold", 0)),
            reset_after=int(cfg.get("reset_after", 300)),
        )


def get_circuit_state_path(log_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(log_dir) / "circuit" / f"{safe}.json"


def load_circuit_state(log_dir: str, job_name: str) -> dict:
    path = get_circuit_state_path(log_dir, job_name)
    if not path.exists():
        return {"consecutive_failures": 0, "opened_at": None}
    with path.open() as fh:
        return json.load(fh)


def save_circuit_state(log_dir: str, job_name: str, state: dict) -> None:
    path = get_circuit_state_path(log_dir, job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(state, fh)


def record_failure(log_dir: str, job_name: str, policy: CircuitBreakerPolicy) -> dict:
    state = load_circuit_state(log_dir, job_name)
    state["consecutive_failures"] += 1
    if policy.enabled and state["consecutive_failures"] >= policy.threshold:
        state["opened_at"] = state.get("opened_at") or time.time()
    save_circuit_state(log_dir, job_name, state)
    return state


def record_success(log_dir: str, job_name: str) -> None:
    save_circuit_state(log_dir, job_name, {"consecutive_failures": 0, "opened_at": None})


def is_open(log_dir: str, job_name: str, policy: CircuitBreakerPolicy) -> bool:
    """Return True if the circuit is open (job should be skipped)."""
    if not policy.enabled:
        return False
    state = load_circuit_state(log_dir, job_name)
    if state["opened_at"] is None:
        return False
    elapsed = time.time() - state["opened_at"]
    if elapsed >= policy.reset_after:
        # Half-open: allow one attempt by resetting opened_at
        state["opened_at"] = None
        save_circuit_state(log_dir, job_name, state)
        return False
    return True
