"""runlog.py — Append-only structured run log for job execution events."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from cronwatch.log import get_log_dir
from cronwatch.runner import JobResult


_RUNLOG_FILENAME = "runlog.jsonl"


@dataclass
class RunLogEntry:
    timestamp: str
    job_name: str
    command: str
    exit_code: int
    duration: float
    success: bool
    stdout_lines: int
    stderr_lines: int
    note: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.job_name:
            raise ValueError("job_name must not be empty")
        if self.duration < 0:
            raise ValueError("duration must be non-negative")


def get_runlog_path(log_dir: Optional[str] = None) -> Path:
    """Return the path to the shared run log file."""
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / _RUNLOG_FILENAME


def _entry_from_result(result: JobResult, job_name: str, note: Optional[str] = None) -> RunLogEntry:
    now = datetime.now(timezone.utc).isoformat()
    stdout_lines = len(result.stdout.splitlines()) if result.stdout else 0
    stderr_lines = len(result.stderr.splitlines()) if result.stderr else 0
    return RunLogEntry(
        timestamp=now,
        job_name=job_name,
        command=result.command,
        exit_code=result.exit_code,
        duration=result.duration,
        success=result.exit_code == 0,
        stdout_lines=stdout_lines,
        stderr_lines=stderr_lines,
        note=note,
    )


def append_run_log(
    result: JobResult,
    job_name: str,
    log_dir: Optional[str] = None,
    note: Optional[str] = None,
) -> RunLogEntry:
    """Append a JobResult to the run log and return the entry."""
    entry = _entry_from_result(result, job_name, note=note)
    path = get_runlog_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
    return entry


def read_run_log(log_dir: Optional[str] = None) -> List[RunLogEntry]:
    """Read all entries from the run log."""
    path = get_runlog_path(log_dir)
    if not path.exists():
        return []
    entries: List[RunLogEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(RunLogEntry(**data))
    return entries


def last_run_entry(job_name: str, log_dir: Optional[str] = None) -> Optional[RunLogEntry]:
    """Return the most recent run log entry for a given job name."""
    entries = [
        e for e in read_run_log(log_dir) if e.job_name == job_name
    ]
    return entries[-1] if entries else None
