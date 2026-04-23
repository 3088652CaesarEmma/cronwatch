"""Context manager that applies stagger delay before a job runs."""
from __future__ import annotations

from cronwatch.stagger import StaggerPolicy


class StaggerGuard:
    """Apply a stagger delay on context entry.

    Usage::

        with StaggerGuard(policy, job_name="backup"):
            run_job()
    """

    def __init__(self, policy: StaggerPolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name

    def __enter__(self) -> "StaggerGuard":
        self._policy.apply(self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False  # never suppress exceptions
