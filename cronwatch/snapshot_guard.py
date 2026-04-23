"""Guard that checks job output against a stored snapshot and optionally alerts on change."""
from __future__ import annotations

from typing import Optional

from cronwatch.snapshots import SnapshotPolicy, output_changed, save_snapshot


class OutputChangedError(Exception):
    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        super().__init__(f"Output snapshot changed for job '{job_name}'")


class SnapshotGuard:
    """Context manager that records and compares output snapshots after a job runs.

    Usage::

        guard = SnapshotGuard(policy, job_name)
        with guard:
            result = run_job(...)
        guard.check(result.stdout)
    """

    def __init__(self, policy: SnapshotPolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name
        self._changed: Optional[bool] = None

    def __enter__(self) -> "SnapshotGuard":
        return self

    def check(self, output: str) -> bool:
        """Compare *output* against stored snapshot. Saves new snapshot and returns True if changed."""
        if not self._policy.enabled:
            return False
        changed = output_changed(self._job_name, output)
        if self._policy.store_output or changed:
            save_snapshot(self._job_name, output)
        self._changed = changed
        if changed and self._policy.alert_on_change:
            raise OutputChangedError(self._job_name)
        return changed

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
