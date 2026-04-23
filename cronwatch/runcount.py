"""Track cumulative run counts per job across all time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from cronwatch.log import get_log_dir
from cronwatch.runner import JobResult


def get_runcount_path(log_dir: str | None = None) -> Path:
    """Return the path to the run-count state file."""
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / "runcount.json"


def load_runcounts(log_dir: str | None = None) -> Dict[str, int]:
    """Load the current run-count mapping from disk.

    Returns an empty dict when the file does not yet exist.
    """
    path = get_runcount_path(log_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_runcounts(counts: Dict[str, int], log_dir: str | None = None) -> None:
    """Persist the run-count mapping to disk."""
    path = get_runcount_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(counts, indent=2))


def increment(job_name: str, log_dir: str | None = None) -> int:
    """Increment the run count for *job_name* and return the new value."""
    counts = load_runcounts(log_dir)
    counts[job_name] = counts.get(job_name, 0) + 1
    save_runcounts(counts, log_dir)
    return counts[job_name]


def get_count(job_name: str, log_dir: str | None = None) -> int:
    """Return the total number of times *job_name* has been run."""
    return load_runcounts(log_dir).get(job_name, 0)


def reset(job_name: str, log_dir: str | None = None) -> None:
    """Reset the run count for *job_name* to zero."""
    counts = load_runcounts(log_dir)
    counts[job_name] = 0
    save_runcounts(counts, log_dir)


def record_result(result: JobResult, log_dir: str | None = None) -> int:
    """Convenience helper: increment the counter for the job in *result*.

    Returns the new cumulative count.
    """
    return increment(result.command, log_dir)
