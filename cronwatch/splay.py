"""Splay policy: spread job starts randomly within a fixed window to avoid thundering herd."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SplayPolicy:
    """Randomly delay a job start by up to *window* seconds.

    Unlike JitterPolicy (which adds noise to a fixed delay), SplayPolicy is
    designed to spread many jobs that would otherwise all fire at the same
    second across a wider window.
    """

    window: float = 0.0  # seconds; 0 disables splay
    seed: Optional[int] = None  # optional RNG seed for deterministic tests

    def __post_init__(self) -> None:
        if not isinstance(self.window, (int, float)):
            raise TypeError("window must be a number")
        if self.window < 0:
            raise ValueError("window must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.window > 0

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SplayPolicy":
        if not cfg:
            return cls()
        window = cfg.get("window", 0.0)
        seed = cfg.get("seed", None)
        return cls(window=float(window), seed=seed)

    def sample(self) -> float:
        """Return a random delay in [0, window) seconds."""
        if not self.enabled:
            return 0.0
        rng = random.Random(self.seed)
        return rng.uniform(0.0, self.window)

    def apply(self) -> float:
        """Sleep for a sampled delay and return the actual delay used."""
        delay = self.sample()
        if delay > 0:
            time.sleep(delay)
        return delay
