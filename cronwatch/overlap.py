"""Overlap detection: prevent a cron job from running if a previous instance is still active."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def get_lock_dir(log_dir: str) -> Path:
    """Return the directory used to store PID lock files."""
    return Path(log_dir) / "locks"


def get_lock_path(log_dir: str, job_name: str) -> Path:
    """Return the PID file path for a given job name."""
    safe_name = job_name.replace("/", "_").replace(" ", "_")
    return get_lock_dir(log_dir) / f"{safe_name}.pid"


def _pid_alive(pid: int) -> bool:
    """Return True if the process with *pid* is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def acquire_lock(log_dir: str, job_name: str) -> bool:
    """Try to acquire a PID lock for *job_name*.

    Returns True if the lock was acquired, False if another instance is
    already running.
    """
    lock_path = get_lock_path(log_dir, job_name)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists():
        try:
            existing_pid = int(lock_path.read_text().strip())
        except (ValueError, OSError):
            existing_pid = None

        if existing_pid is not None and _pid_alive(existing_pid):
            return False
        # Stale lock — remove it
        lock_path.unlink(missing_ok=True)

    lock_path.write_text(str(os.getpid()))
    return True


def release_lock(log_dir: str, job_name: str) -> None:
    """Release the PID lock for *job_name* if it belongs to the current process."""
    lock_path = get_lock_path(log_dir, job_name)
    if lock_path.exists():
        try:
            stored_pid = int(lock_path.read_text().strip())
        except (ValueError, OSError):
            stored_pid = None
        if stored_pid == os.getpid():
            lock_path.unlink(missing_ok=True)


def is_locked(log_dir: str, job_name: str) -> bool:
    """Return True if *job_name* has an active lock from another process."""
    lock_path = get_lock_path(log_dir, job_name)
    if not lock_path.exists():
        return False
    try:
        pid = int(lock_path.read_text().strip())
    except (ValueError, OSError):
        return False
    return _pid_alive(pid) and pid != os.getpid()
