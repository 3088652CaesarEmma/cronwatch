"""Guard that enforces minimum-priority requirements before running a job."""
from __future__ import annotations

from typing import Optional

from cronwatch.priority import PriorityPolicy, DEFAULT_PRIORITY


class PriorityViolationError(Exception):
    """Raised when a job's priority is below the required minimum."""

    def __init__(self, job_name: str, actual: int, required: int) -> None:
        self.job_name = job_name
        self.actual = actual
        self.required = required
        super().__init__(
            f"Job '{job_name}' has priority {actual}, "
            f"but minimum required is {required}."
        )


class PriorityGuard:
    """Context manager that blocks jobs whose priority is below *min_priority*.

    Parameters
    ----------
    job_name:
        Name of the job being guarded (used in error messages).
    policy:
        The job's :class:`PriorityPolicy`.
    min_priority:
        The floor priority required to proceed.  Defaults to 0 (always pass).
    """

    def __init__(
        self,
        job_name: str,
        policy: PriorityPolicy,
        min_priority: int = 0,
    ) -> None:
        self._job_name = job_name
        self._policy = policy
        self._min_priority = min_priority

    def __enter__(self) -> "PriorityGuard":
        if self._policy.priority < self._min_priority:
            raise PriorityViolationError(
                self._job_name, self._policy.priority, self._min_priority
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None
