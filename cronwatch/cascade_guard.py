"""CascadeGuard: enqueues downstream jobs after a job completes."""
from __future__ import annotations

from typing import Callable, List, Optional

from cronwatch.cascade import CascadePolicy
from cronwatch.runner import JobResult


class CascadeGuard:
    """Context manager that triggers downstream jobs based on job outcome.

    The *trigger* callable receives a list of job names to run next.
    It is the caller's responsibility to resolve and execute those jobs.
    """

    def __init__(
        self,
        policy: CascadePolicy,
        trigger: Callable[[List[str]], None],
    ) -> None:
        self._policy = policy
        self._trigger = trigger
        self._result: Optional[JobResult] = None

    def __enter__(self) -> "CascadeGuard":
        return self

    def set_result(self, result: JobResult) -> None:
        """Record the job result so the guard can act on exit."""
        self._result = result

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._policy.enabled:
            return False
        if self._result is None:
            return False
        success = self._result.exit_code == 0
        downstream = self._policy.jobs_for(success)
        if downstream:
            self._trigger(downstream)
        return False
