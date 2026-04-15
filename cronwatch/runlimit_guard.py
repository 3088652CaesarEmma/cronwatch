"""Context-manager guard that enforces RunLimitPolicy for a job."""
from __future__ import annotations

from cronwatch.runlimit import RunLimitPolicy, check_run_limit, record_run


class RunLimitExceededError(Exception):
    """Raised when a job has exceeded its allowed run count in the window."""

    def __init__(self, job_name: str, max_runs: int, window_seconds: int) -> None:
        self.job_name = job_name
        self.max_runs = max_runs
        self.window_seconds = window_seconds
        super().__init__(
            f"Job '{job_name}' has exceeded {max_runs} runs "
            f"in the last {window_seconds}s window."
        )


class RunLimitGuard:
    """Allows a job to proceed only if it is within its run-count limit.

    On successful __enter__ the run is recorded so it counts against future
    checks within the same rolling window.
    """

    def __init__(
        self,
        policy: RunLimitPolicy,
        log_dir: str,
        job_name: str,
    ) -> None:
        self._policy = policy
        self._log_dir = log_dir
        self._job_name = job_name

    def __enter__(self) -> "RunLimitGuard":
        if not check_run_limit(self._policy, self._log_dir, self._job_name):
            raise RunLimitExceededError(
                self._job_name,
                self._policy.max_runs,
                self._policy.window_seconds,
            )
        record_run(self._policy, self._log_dir, self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        return None
