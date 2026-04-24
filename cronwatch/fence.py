"""fence.py — Execution fence: prevent a job from running outside a defined
date range (not-before / not-after).  Complements ExpiryPolicy (which only
checks a single end-date) by also enforcing an optional start date.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


class FenceViolationError(Exception):
    """Raised when a job is executed outside its allowed date fence."""

    def __init__(self, job_name: str, reason: str) -> None:
        self.job_name = job_name
        self.reason = reason
        super().__init__(f"Job '{job_name}' blocked by fence: {reason}")


@dataclass
class FencePolicy:
    """Date-range fence for a cron job."""

    not_before: Optional[datetime.date] = None
    not_after: Optional[datetime.date] = None

    def __post_init__(self) -> None:
        if self.not_before is not None and not isinstance(self.not_before, datetime.date):
            raise TypeError("not_before must be a datetime.date or None")
        if self.not_after is not None and not isinstance(self.not_after, datetime.date):
            raise TypeError("not_after must be a datetime.date or None")
        if (
            self.not_before is not None
            and self.not_after is not None
            and self.not_before > self.not_after
        ):
            raise ValueError("not_before must not be later than not_after")

    # ------------------------------------------------------------------
    @property
    def enabled(self) -> bool:
        return self.not_before is not None or self.not_after is not None

    def check(self, job_name: str, today: Optional[datetime.date] = None) -> None:
        """Raise FenceViolationError if *today* is outside the fence."""
        if not self.enabled:
            return
        today = today or datetime.date.today()
        if self.not_before is not None and today < self.not_before:
            raise FenceViolationError(
                job_name,
                f"before activation date {self.not_before.isoformat()}",
            )
        if self.not_after is not None and today > self.not_after:
            raise FenceViolationError(
                job_name,
                f"after expiry date {self.not_after.isoformat()}",
            )

    # ------------------------------------------------------------------
    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "FencePolicy":
        if not cfg:
            return cls()
        not_before = cfg.get("not_before")
        not_after = cfg.get("not_after")
        if isinstance(not_before, str):
            not_before = datetime.date.fromisoformat(not_before)
        if isinstance(not_after, str):
            not_after = datetime.date.fromisoformat(not_after)
        return cls(not_before=not_before, not_after=not_after)


class FenceGuard:
    """Context manager that enforces a FencePolicy before the job body runs."""

    def __init__(self, policy: FencePolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name

    def __enter__(self) -> "FenceGuard":
        self._policy.check(self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
