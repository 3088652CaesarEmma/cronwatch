"""Checkpoint support: persist and query the last successful run time for a job."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir

_CHECKPOINT_FILE = "checkpoints.json"


def get_checkpoint_path(log_dir: Optional[str] = None) -> Path:
    """Return the path to the checkpoint state file."""
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / _CHECKPOINT_FILE


def load_checkpoints(log_dir: Optional[str] = None) -> dict[str, str]:
    """Load all checkpoint timestamps from disk.  Returns an empty dict if none exist."""
    path = get_checkpoint_path(log_dir)
    if not path.exists():
        return {}
    try:
        with path.open() as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_checkpoints(checkpoints: dict[str, str], log_dir: Optional[str] = None) -> None:
    """Persist the checkpoint mapping to disk."""
    path = get_checkpoint_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(checkpoints, fh, indent=2)


def record_success(job_name: str, log_dir: Optional[str] = None, ts: Optional[datetime] = None) -> None:
    """Record a successful completion timestamp for *job_name*."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    checkpoints = load_checkpoints(log_dir)
    checkpoints[job_name] = ts.isoformat()
    save_checkpoints(checkpoints, log_dir)


def last_success(job_name: str, log_dir: Optional[str] = None) -> Optional[datetime]:
    """Return the last successful run time for *job_name*, or *None* if never recorded."""
    checkpoints = load_checkpoints(log_dir)
    raw = checkpoints.get(job_name)
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def seconds_since_success(job_name: str, log_dir: Optional[str] = None) -> Optional[float]:
    """Return elapsed seconds since the last successful run, or *None* if never run."""
    ts = last_success(job_name, log_dir)
    if ts is None:
        return None
    now = datetime.now(timezone.utc)
    # Ensure both are offset-aware for subtraction
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now - ts).total_seconds()
