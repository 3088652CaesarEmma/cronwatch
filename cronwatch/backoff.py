"""Exponential backoff calculation utilities for retry and rate-limit logic."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BackoffPolicy:
    """Defines how wait times grow between successive retry attempts."""

    base_delay: float = 1.0        # seconds before first retry
    multiplier: float = 2.0        # factor applied each attempt
    max_delay: float = 300.0       # cap on any single wait (5 min)
    jitter: float = 0.0            # random fraction added (0.0–1.0)

    def __post_init__(self) -> None:
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if not (0.0 <= self.jitter <= 1.0):
            raise ValueError("jitter must be between 0.0 and 1.0")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "BackoffPolicy":
        if not cfg:
            return cls()
        return cls(
            base_delay=float(cfg.get("base_delay", 1.0)),
            multiplier=float(cfg.get("multiplier", 2.0)),
            max_delay=float(cfg.get("max_delay", 300.0)),
            jitter=float(cfg.get("jitter", 0.0)),
        )

    def delay_for(self, attempt: int) -> float:
        """Return the wait time (seconds) before *attempt* (0-indexed).

        Attempt 0 is the first retry; the initial run is not counted.
        """
        if attempt < 0:
            raise ValueError("attempt must be >= 0")
        raw = self.base_delay * (self.multiplier ** attempt)
        capped = min(raw, self.max_delay)
        if self.jitter > 0.0:
            import random
            capped += random.uniform(0, self.jitter * capped)
        return capped

    def delays(self, attempts: int) -> list[float]:
        """Return a list of delay values for *attempts* retries."""
        return [self.delay_for(i) for i in range(attempts)]

    @property
    def enabled(self) -> bool:
        return self.base_delay > 0.0
