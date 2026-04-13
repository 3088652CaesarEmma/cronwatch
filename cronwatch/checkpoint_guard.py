"""CheckpointGuard: context manager that records a checkpoint on successful job completion."""

from __future__ import annotations

from typing import Optional

from cronwatch.checkpoint import record_success
from cronwatch.runner import JobResult


class CheckpointGuard:
    """Records a checkpoint for *job_name* when the wrapped :class:`JobResult` succeeds.

    Usage::

        result = run_job(entry)
        with CheckpointGuard("my_job", log_dir=log_dir) as guard:
            guard.commit(result)
    """

    def __init__(self, job_name: str, log_dir: Optional[str] = None) -> None:
        if not job_name or not job_name.strip():
            raise ValueError("job_name must be a non-empty string")
        self.job_name = job_name
        self.log_dir = log_dir
        self._committed = False

    def __enter__(self) -> "CheckpointGuard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:  # type: ignore[override]
        # Do not suppress exceptions; checkpoint is only written via commit().
        return False

    def commit(self, result: JobResult) -> bool:
        """Write a checkpoint if *result* indicates success (exit code 0).

        Returns *True* if a checkpoint was recorded, *False* otherwise.
        """
        if result.exit_code == 0:
            record_success(self.job_name, self.log_dir)
            self._committed = True
            return True
        return False

    @property
    def committed(self) -> bool:
        """True if a checkpoint has been recorded during this guard's lifetime."""
        return self._committed


def maybe_checkpoint(job_name: str, result: JobResult, log_dir: Optional[str] = None) -> bool:
    """Convenience function: record a checkpoint for *job_name* if *result* succeeded.

    Returns *True* when a checkpoint was written.
    """
    with CheckpointGuard(job_name, log_dir=log_dir) as guard:
        return guard.commit(result)
