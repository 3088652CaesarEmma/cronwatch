"""Drain policy: wait for in-flight jobs to finish before shutdown."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DrainPolicy:
    """Configuration for graceful drain behaviour on shutdown."""

    timeout: float = 30.0  # seconds to wait for in-flight jobs
    poll_interval: float = 0.25  # seconds between readiness checks

    def __post_init__(self) -> None:
        if self.timeout < 0:
            raise ValueError("DrainPolicy.timeout must be >= 0")
        if self.poll_interval <= 0:
            raise ValueError("DrainPolicy.poll_interval must be > 0")

    @property
    def enabled(self) -> bool:
        return self.timeout > 0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "DrainPolicy":
        if not cfg:
            return cls()
        return cls(
            timeout=float(cfg.get("timeout", 30.0)),
            poll_interval=float(cfg.get("poll_interval", 0.25)),
        )


class DrainCoordinator:
    """Tracks active jobs and blocks shutdown until all finish or timeout."""

    def __init__(self, policy: DrainPolicy) -> None:
        self._policy = policy
        self._lock = threading.Lock()
        self._active: set[str] = set()

    def acquire(self, job_name: str) -> None:
        """Register a job as in-flight."""
        with self._lock:
            self._active.add(job_name)

    def release(self, job_name: str) -> None:
        """Mark a job as finished."""
        with self._lock:
            self._active.discard(job_name)

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    @property
    def active_jobs(self) -> list[str]:
        with self._lock:
            return sorted(self._active)

    def drain(self) -> bool:
        """Block until all jobs finish or timeout elapses.

        Returns True if all jobs finished, False if timed out.
        """
        if not self._policy.enabled:
            return True

        deadline = time.monotonic() + self._policy.timeout
        while time.monotonic() < deadline:
            if self.active_count == 0:
                return True
            time.sleep(self._policy.poll_interval)
        return self.active_count == 0
