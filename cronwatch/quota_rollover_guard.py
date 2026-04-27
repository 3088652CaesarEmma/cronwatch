"""Guard that triggers quota rollover before a job runs."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwatch.quota import load_quota_state, save_quota_state
from cronwatch.quota_rollover import QuotaRolloverPolicy, maybe_rollover


class QuotaRolloverGuard:
    """Context manager that resets quota state when a rollover period boundary is crossed."""

    def __init__(
        self,
        job_name: str,
        policy: QuotaRolloverPolicy,
        log_dir: Optional[Path] = None,
    ) -> None:
        self._job_name = job_name
        self._policy = policy
        self._log_dir = log_dir
        self.rolled_over: bool = False

    def __enter__(self) -> "QuotaRolloverGuard":
        if maybe_rollover(self._job_name, self._policy, self._log_dir):
            self.rolled_over = True
            # Wipe the quota run-log so counts start fresh
            save_quota_state(self._job_name, [], self._log_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
