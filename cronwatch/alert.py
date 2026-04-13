"""Alert throttling and deduplication for cronwatch notifications."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


@dataclass
class AlertState:
    job_name: str
    last_alerted_at: float
    consecutive_failures: int = 0
    suppressed_count: int = 0


def get_alert_state_path(log_dir: Optional[Path] = None) -> Path:
    base = log_dir or get_log_dir()
    return base / "alert_state.json"


def load_alert_states(log_dir: Optional[Path] = None) -> dict[str, AlertState]:
    path = get_alert_state_path(log_dir)
    if not path.exists():
        return {}
    with path.open() as f:
        raw = json.load(f)
    return {
        name: AlertState(**data)
        for name, data in raw.items()
    }


def save_alert_states(states: dict[str, AlertState], log_dir: Optional[Path] = None) -> None:
    path = get_alert_state_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(
            {name: vars(state) for name, state in states.items()},
            f,
            indent=2,
        )


def should_alert(
    job_name: str,
    succeeded: bool,
    cooldown_seconds: int = 3600,
    log_dir: Optional[Path] = None,
) -> bool:
    """Return True if an alert should be sent, applying cooldown throttling."""
    states = load_alert_states(log_dir)
    now = time.time()
    state = states.get(job_name)

    if succeeded:
        if state is not None:
            del states[job_name]
            save_alert_states(states, log_dir)
        return False

    if state is None:
        states[job_name] = AlertState(
            job_name=job_name,
            last_alerted_at=now,
            consecutive_failures=1,
        )
        save_alert_states(states, log_dir)
        return True

    state.consecutive_failures += 1
    elapsed = now - state.last_alerted_at

    if elapsed >= cooldown_seconds:
        state.last_alerted_at = now
        state.suppressed_count = 0
        save_alert_states(states, log_dir)
        return True

    state.suppressed_count += 1
    save_alert_states(states, log_dir)
    return False


def reset_alert_state(job_name: str, log_dir: Optional[Path] = None) -> None:
    states = load_alert_states(log_dir)
    states.pop(job_name, None)
    save_alert_states(states, log_dir)
