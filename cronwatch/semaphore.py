"""Named semaphore policy for limiting parallel job slots across processes."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


@dataclass
class SemaphorePolicy:
    name: str = ""
    slots: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.slots, int) or isinstance(self.slots, bool):
            raise TypeError("slots must be an integer")
        if self.slots < 1:
            raise ValueError("slots must be >= 1")
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")

    @property
    def enabled(self) -> bool:
        return bool(self.name)

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SemaphorePolicy":
        if not cfg:
            return cls()
        return cls(
            name=str(cfg.get("name", "")),
            slots=int(cfg.get("slots", 1)),
        )


def get_semaphore_path(name: str, log_dir: Optional[str] = None) -> Path:
    base = Path(log_dir) if log_dir else get_log_dir()
    return base / "semaphores" / f"{name}.json"


def _load(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save(path: Path, holders: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(holders))


def acquire_semaphore(policy: SemaphorePolicy, job_name: str,
                      log_dir: Optional[str] = None) -> bool:
    """Try to acquire a slot. Returns True if acquired, False if full."""
    path = get_semaphore_path(policy.name, log_dir)
    holders = [h for h in _load(path) if _pid_alive(h["pid"])]
    if len(holders) >= policy.slots:
        _save(path, holders)
        return False
    holders.append({"job": job_name, "pid": os.getpid(), "ts": time.time()})
    _save(path, holders)
    return True


def release_semaphore(policy: SemaphorePolicy, log_dir: Optional[str] = None) -> None:
    """Release this process's slot."""
    path = get_semaphore_path(policy.name, log_dir)
    pid = os.getpid()
    holders = [h for h in _load(path) if h["pid"] != pid and _pid_alive(h["pid"])]
    _save(path, holders)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
