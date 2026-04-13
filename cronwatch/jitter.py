"""Jitter policy: add randomised delay before running a job to spread load."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterPolicy:
    """Controls optional random sleep before a job executes."""

    max_seconds: int = 0
    enabled: bool = field(init=False)

    def __post_init__(self) -> None:
        if self.max_seconds < 0:
            raise ValueError("jitter max_seconds must be >= 0")
        self.enabled = self.max_seconds > 0

    # ------------------------------------------------------------------
    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "JitterPolicy":
        """Build a JitterPolicy from a config dict (or None for defaults)."""
        if not cfg:
            return cls()
        return cls(max_seconds=int(cfg.get("max_seconds", 0)))

    # ------------------------------------------------------------------
    def sample(self) -> float:
        """Return a random delay in [0, max_seconds]."""
        if not self.enabled:
            return 0.0
        return random.uniform(0, self.max_seconds)

    def apply(self) -> float:
        """Sleep for a random duration and return how long we slept."""
        delay = self.sample()
        if delay > 0:
            time.sleep(delay)
        return delay
