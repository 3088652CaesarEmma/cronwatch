"""Guard that raises when a job is paused, preventing execution."""

from __future__ import annotations

from cronwatch.pause import is_paused


class JobPausedError(Exception):
    """Raised when a job is skipped because it is paused."""

    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        super().__init__(f"Job '{job_name}' is paused and will not run.")


class PauseGuard:
    """Context manager that blocks execution when a job is paused.

    Usage::

        with PauseGuard(job_name, log_dir=log_dir):
            run_job(...)
    """

    def __init__(self, job_name: str, log_dir: str | None = None) -> None:
        self.job_name = job_name
        self.log_dir = log_dir

    def __enter__(self) -> "PauseGuard":
        if is_paused(self.job_name, self.log_dir):
            raise JobPausedError(self.job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:  # type: ignore[override]
        return False
