"""Guard that skips a job when a maintenance window is active."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from cronwatch.maintenance import MaintenancePolicy


class MaintenanceActiveError(Exception):
    """Raised when a job is skipped due to an active maintenance window."""

    def __init__(self, job_name: str, dt: datetime) -> None:
        self.job_name = job_name
        self.dt = dt
        super().__init__(
            f"Job {job_name!r} skipped: maintenance window active at {dt.strftime('%H:%M')}"
        )


class MaintenanceGuard:
    """Context manager that raises MaintenanceActiveError inside a maintenance window."""

    def __init__(self, policy: MaintenancePolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name

    def __enter__(self) -> "MaintenanceGuard":
        if self._policy.enabled():
            now = datetime.now()
            if self._policy.is_active(now):
                raise MaintenanceActiveError(self._job_name, now)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
