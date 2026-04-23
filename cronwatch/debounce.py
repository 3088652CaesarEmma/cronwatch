"""Debounce policy: suppress repeated notifications until a quiet period elapses."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


@dataclass
class DebouncePolicy:
    """Suppress repeated failure alerts until *window_seconds* of silence pass."""

    window_seconds: int = 0  # 0 = disabled

    def __post_init__(self) -> None:
        if self.window_seconds < 0:
            raise ValueError("window_seconds must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.window_seconds > 0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "DebouncePolicy":
        if not cfg:
            return cls()
        return cls(window_seconds=int(cfg.get("window_seconds", 0)))


def get_debounce_state_path(job_name: str, log_dir: Optional[Path] = None) -> Path:
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / "debounce" / f"{job_name}.json"


def load_debounce_state(job_name: str, log_dir: Optional[Path] = None) -> dict:
    path = get_debounce_state_path(job_name, log_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_debounce_state(job_name: str, state: dict, log_dir: Optional[Path] = None) -> None:
    path = get_debounce_state_path(job_name, log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def should_debounce(policy: DebouncePolicy, job_name: str, log_dir: Optional[Path] = None) -> bool:
    """Return True if the notification should be suppressed (debounced)."""
    if not policy.enabled:
        return False
    state = load_debounce_state(job_name, log_dir)
    last_fired: float = state.get("last_fired", 0.0)
    return (time.time() - last_fired) < policy.window_seconds


def record_fired(job_name: str, log_dir: Optional[Path] = None) -> None:
    """Record that a notification was fired right now."""
    state = load_debounce_state(job_name, log_dir)
    state["last_fired"] = time.time()
    save_debounce_state(job_name, state, log_dir)
