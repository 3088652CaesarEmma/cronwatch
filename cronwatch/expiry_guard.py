"""Guard that raises JobExpiredError if the job's expiry policy has lapsed."""
from __future__ import annotations
from datetime import date
from typing import Optional

from cronwatch.expiry import ExpiryPolicy, JobExpiredError


class ExpiryGuard:
    """Context manager that blocks execution of expired jobs."""

    def __init__(self, policy: ExpiryPolicy, job_name: str,
                 today: Optional[date] = None):
        self.policy = policy
        self.job_name = job_name
        self.today = today

    def __enter__(self) -> "ExpiryGuard":
        if self.policy.is_expired(self.today):
            raise JobExpiredError(self.job_name, self.policy.expires_on)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
