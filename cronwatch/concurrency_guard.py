"""Context manager that enforces the ConcurrencyPolicy for a job run."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwatch.concurrency import (
    ConcurrencyPolicy,
    can_run,
    register_running,
    deregister_running,
)


class ConcurrencyLimitError(RuntimeError):
    """Raised when the concurrency limit is reached and the job cannot start."""


class ConcurrencyGuard:
    """Acquire a concurrency slot for a job or raise ConcurrencyLimitError.

    Usage::

        policy = ConcurrencyPolicy(max_jobs=2)
        with ConcurrencyGuard(policy, job_name="backup"):
            run_job(...)
    """

    def __init__(
        self,
        policy: ConcurrencyPolicy,
        job_name: str,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.policy = policy
        self.job_name = job_name
        self.log_dir = log_dir
        self._registered = False

    def __enter__(self) -> "ConcurrencyGuard":
        if not can_run(self.policy, self.log_dir):
            raise ConcurrencyLimitError(
                f"Concurrency limit of {self.policy.max_jobs} reached; "
                f"job '{self.job_name}' will not run."
            )
        register_running(self.job_name, self.log_dir)
        self._registered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._registered:
            deregister_running(self.log_dir)
            self._registered = False
        return False  # do not suppress exceptions
