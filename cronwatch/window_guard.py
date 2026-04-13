"""Context manager that enforces WindowPolicy before running a job."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from cronwatch.window import WindowPolicy


class WindowViolationError(Exception):
    """Raised when a job is attempted outside its allowed time windows."""

    def __init__(self, job_name: str, dt: datetime) -> None:
        self.job_name = job_name
        self.dt = dt
        super().__init__(
            f"Job {job_name!r} is not allowed to run at "
            f"{dt.strftime('%H:%M')} — outside configured time windows."
        )


class WindowGuard:
    """Raise WindowViolationError if the current time is outside policy windows.

    Usage::

        with WindowGuard(policy, job_name="backup"):
            run_job(...)
    """

    def __init__(
        self,
        policy: WindowPolicy,
        job_name: str = "",
        now: Optional[datetime] = None,
    ) -> None:
        self._policy = policy
        self._job_name = job_name
        self._now = now  # injectable for testing

    def __enter__(self) -> "WindowGuard":
        dt = self._now or datetime.now()
        if not self._policy.is_allowed(dt):
            raise WindowViolationError(self._job_name, dt)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False  # never suppress exceptions
