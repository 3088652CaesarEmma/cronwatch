"""Context manager guard that enforces PinPolicy before a job runs."""
from __future__ import annotations

from cronwatch.pin import PinPolicy, PinViolationError


class PinGuard:
    """Raises PinViolationError on __enter__ if schedule pin is violated.

    Usage::

        policy = PinPolicy(schedule="0 * * * *")
        with PinGuard(policy, job_name="backup", actual_schedule="0 * * * *"):
            run_job()
    """

    def __init__(
        self,
        policy: PinPolicy,
        job_name: str,
        actual_schedule: str,
    ) -> None:
        self._policy = policy
        self._job_name = job_name
        self._actual_schedule = actual_schedule

    def __enter__(self) -> "PinGuard":
        self._policy.check(self._job_name, self._actual_schedule)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
