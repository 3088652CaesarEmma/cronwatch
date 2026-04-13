"""Concurrency policy: limit how many jobs run simultaneously."""

from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from cronwatch.log import get_log_dir

_CONCURRENCY_STATE_FILE = "concurrency_state.json"


@dataclass
class ConcurrencyPolicy:
    max_jobs: int = 0  # 0 = unlimited

    def __post_init__(self) -> None:
        if not isinstance(self.max_jobs, int) or self.max_jobs < 0:
            raise ValueError("max_jobs must be a non-negative integer")

    @property
    def enabled(self) -> bool:
        return self.max_jobs > 0

    @classmethod
    def from_config(cls, cfg: dict | None) -> "ConcurrencyPolicy":
        if not cfg:
            return cls()
        return cls(max_jobs=int(cfg.get("max_jobs", 0)))


def get_concurrency_state_path(log_dir: Path | None = None) -> Path:
    base = log_dir or get_log_dir()
    return base / _CONCURRENCY_STATE_FILE


def _load_state(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_state(path: Path, entries: List[dict]) -> None:
    path.write_text(json.dumps(entries, indent=2))


def running_count(log_dir: Path | None = None) -> int:
    """Return the number of currently tracked running jobs."""
    path = get_concurrency_state_path(log_dir)
    entries = _load_state(path)
    alive = [e for e in entries if _pid_alive(e["pid"])]
    if len(alive) != len(entries):
        _save_state(path, alive)
    return len(alive)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def register_running(job_name: str, log_dir: Path | None = None) -> None:
    """Record the current process as running a job."""
    path = get_concurrency_state_path(log_dir)
    entries = _load_state(path)
    entries = [e for e in entries if _pid_alive(e["pid"])]
    entries.append({"job": job_name, "pid": os.getpid(), "started": time.time()})
    _save_state(path, entries)


def deregister_running(log_dir: Path | None = None) -> None:
    """Remove the current process from the running jobs list."""
    path = get_concurrency_state_path(log_dir)
    pid = os.getpid()
    entries = [e for e in _load_state(path) if e["pid"] != pid]
    _save_state(path, entries)


def can_run(policy: ConcurrencyPolicy, log_dir: Path | None = None) -> bool:
    """Return True if a new job is allowed to start under the given policy."""
    if not policy.enabled:
        return True
    return running_count(log_dir) < policy.max_jobs
