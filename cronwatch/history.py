"""Persistent job run history tracking for cronwatch."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from cronwatch.log import get_log_dir
from cronwatch.runner import JobResult

HISTORY_FILENAME = "history.jsonl"


def get_history_path(log_dir: Optional[Path] = None) -> Path:
    """Return path to the history file."""
    base = log_dir or get_log_dir()
    return Path(base) / HISTORY_FILENAME


def append_history(result: JobResult, log_dir: Optional[Path] = None) -> None:
    """Append a job result to the history file as a JSONL entry."""
    path = get_history_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "job_name": result.job_name,
        "command": result.command,
        "exit_code": result.exit_code,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "finished_at": result.finished_at.isoformat() if result.finished_at else None,
        "duration_seconds": result.duration_seconds,
        "success": result.success,
    }

    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_history(
    job_name: Optional[str] = None,
    limit: int = 100,
    log_dir: Optional[Path] = None,
) -> List[dict]:
    """Read history entries, optionally filtered by job name.

    Returns entries in reverse-chronological order (most recent first).
    """
    path = get_history_path(log_dir)
    if not path.exists():
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if job_name is None or entry.get("job_name") == job_name:
                entries.append(entry)

    return list(reversed(entries))[:limit]


def last_run(job_name: str, log_dir: Optional[Path] = None) -> Optional[dict]:
    """Return the most recent history entry for a given job, or None."""
    entries = read_history(job_name=job_name, limit=1, log_dir=log_dir)
    return entries[0] if entries else None
