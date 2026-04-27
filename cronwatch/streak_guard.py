"""Guard that records job streaks and optionally alerts on long failure runs."""
from __future__ import annotations

from typing import Optional

from cronwatch.runner import JobResult
from cronwatch.streak import StreakState, record_streak


class StreakGuard:
    """Context manager that updates the streak state after a job finishes.

    Usage::

        with StreakGuard(job_name, log_dir=log_dir) as g:
            result = run_job(command)
            g.set_result(result)
    """

    def __init__(self, job_name: str, log_dir: Optional[str] = None) -> None:
        self.job_name = job_name
        self.log_dir = log_dir
        self._result: Optional[JobResult] = None
        self.state: Optional[StreakState] = None

    def set_result(self, result: JobResult) -> None:
        self._result = result

    def __enter__(self) -> "StreakGuard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._result is not None:
            kwargs = {}
            if self.log_dir is not None:
                kwargs["log_dir"] = self.log_dir
            self.state = record_streak(self._result, **kwargs)
        return False
