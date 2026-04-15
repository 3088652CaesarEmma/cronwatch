"""Pause/resume support for cron jobs.

Allows individual jobs or all jobs to be paused so they are skipped
during scheduled runs without being removed from the config.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from cronwatch.log import get_log_dir

_PAUSE_FILE = "paused_jobs.json"


def get_pause_state_path(log_dir: str | None = None) -> Path:
    """Return path to the pause state file."""
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / _PAUSE_FILE


def load_pause_state(log_dir: str | None = None) -> Dict[str, bool]:
    """Load the pause state mapping {job_name: True} from disk."""
    path = get_pause_state_path(log_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {k: bool(v) for k, v in data.items()}


def save_pause_state(state: Dict[str, bool], log_dir: str | None = None) -> None:
    """Persist the pause state mapping to disk."""
    path = get_pause_state_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(state, fh, indent=2)


def pause_job(job_name: str, log_dir: str | None = None) -> None:
    """Mark a job as paused."""
    state = load_pause_state(log_dir)
    state[job_name] = True
    save_pause_state(state, log_dir)


def resume_job(job_name: str, log_dir: str | None = None) -> None:
    """Remove the pause flag for a job."""
    state = load_pause_state(log_dir)
    state.pop(job_name, None)
    save_pause_state(state, log_dir)


def is_paused(job_name: str, log_dir: str | None = None) -> bool:
    """Return True if the given job is currently paused."""
    state = load_pause_state(log_dir)
    return bool(state.get(job_name, False))


def list_paused(log_dir: str | None = None) -> list[str]:
    """Return a sorted list of all currently paused job names."""
    state = load_pause_state(log_dir)
    return sorted(k for k, v in state.items() if v)
