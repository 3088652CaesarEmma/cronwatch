"""Guard that enforces an optional maximum lifetime run count for a job."""
from __future__ import annotations

from cronwatch.runcount import get_count, increment


class RunCountExceededError(Exception):
    """Raised when a job has reached its maximum lifetime run count."""

    def __init__(self, job_name: str, max_runs: int, current: int) -> None:
        self.job_name = job_name
        self.max_runs = max_runs
        self.current = current
        super().__init__(
            f"Job '{job_name}' has reached its maximum lifetime run count "
            f"({current}/{max_runs})."
        )


class RunCountGuard:
    """Context manager that gates execution on a per-job lifetime run limit.

    Parameters
    ----------
    job_name:
        Identifier used to look up and update the persistent counter.
    max_runs:
        Maximum number of times the job may run in total.  A value of
        ``0`` or ``None`` disables the guard (no limit enforced).
    log_dir:
        Optional override for the directory that holds state files.
    """

    def __init__(
        self,
        job_name: str,
        max_runs: int | None = None,
        log_dir: str | None = None,
    ) -> None:
        self.job_name = job_name
        self.max_runs = max_runs or 0
        self.log_dir = log_dir

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "RunCountGuard":
        if self.max_runs <= 0:
            return self

        current = get_count(self.job_name, self.log_dir)
        if current >= self.max_runs:
            raise RunCountExceededError(self.job_name, self.max_runs, current)

        increment(self.job_name, self.log_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # Never suppress exceptions.
        return False
