"""Context-manager guard that enforces the SkipPolicy before a job runs."""
from __future__ import annotations

from cronwatch.skip import JobSkippedError, SkipPolicy


class SkipGuard:
    """Raises JobSkippedError on __enter__ when the skip condition is met.

    Usage::

        with SkipGuard(policy, job_name="backup"):
            run_job()
    """

    def __init__(self, policy: SkipPolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name

    def __enter__(self) -> "SkipGuard":
        if self._policy.enabled and self._policy.should_skip():
            raise JobSkippedError(
                self._job_name,
                f"skip_if command exited 0: {self._policy.skip_if}",
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
