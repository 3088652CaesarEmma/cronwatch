"""Stagger policy: spread job starts across a time window to avoid thundering herd."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StaggerPolicy:
    """Distribute job start times deterministically within a window."""

    window_seconds: int = 0
    seed: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.window_seconds, int):
            raise TypeError("window_seconds must be an int")
        if self.window_seconds < 0:
            raise ValueError("window_seconds must be >= 0")
        if self.seed is not None and not isinstance(self.seed, str):
            raise TypeError("seed must be a str or None")

    @property
    def enabled(self) -> bool:
        return self.window_seconds > 0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "StaggerPolicy":
        if not cfg:
            return cls()
        return cls(
            window_seconds=int(cfg.get("window_seconds", 0)),
            seed=cfg.get("seed"),
        )

    def delay_for(self, job_name: str) -> float:
        """Return a deterministic delay in seconds for the given job name."""
        if not self.enabled:
            return 0.0
        key = f"{self.seed or ''}:{job_name}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        fraction = int(digest[:8], 16) / 0xFFFFFFFF
        return fraction * self.window_seconds

    def apply(self, job_name: str) -> None:
        """Sleep for the staggered delay appropriate for *job_name*."""
        delay = self.delay_for(job_name)
        if delay > 0:
            time.sleep(delay)
