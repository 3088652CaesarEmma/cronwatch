"""Context manager that enforces quota before allowing a job to execute."""

from __future__ import annotations

from cronwatch.quota import QuotaPolicy, check_quota, record_quota_run


class QuotaExceededError(Exception):
    """Raised when a job has exceeded its configured run quota."""

    def __init__(self, job_name: str, max_runs: int, window_seconds: int) -> None:
        super().__init__(
            f"Job '{job_name}' has reached its quota of {max_runs} run(s) "
            f"within the last {window_seconds}s."
        )
        self.job_name = job_name
        self.max_runs = max_runs
        self.window_seconds = window_seconds


class QuotaGuard:
    """Context manager that checks and records quota usage.

    Usage::

        with QuotaGuard(policy, log_dir, job_name):
            run_job(...)  # only reached if quota allows it
    """

    def __init__(self, policy: QuotaPolicy, log_dir: str, job_name: str) -> None:
        self._policy = policy
        self._log_dir = log_dir
        self._job_name = job_name

    def __enter__(self) -> "QuotaGuard":
        if not check_quota(self._policy, self._log_dir, self._job_name):
            raise QuotaExceededError(
                self._job_name,
                self._policy.max_runs,
                self._policy.window_seconds,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # Record the run only when no exception escaped (job ran successfully
        # enough to count against the quota).
        if exc_type is None or not issubclass(exc_type, QuotaExceededError):
            record_quota_run(self._policy, self._log_dir, self._job_name)
        return False  # never suppress exceptions
