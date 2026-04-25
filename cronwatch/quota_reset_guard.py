"""Context manager that resets the quota counter when the reset policy fires."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwatch.quota import QuotaPolicy, load_quota_state, save_quota_state
from cronwatch.quota_reset import (
    QuotaResetPolicy,
    record_reset,
    should_reset,
)


class QuotaResetGuard:
    """Resets the quota counter for *job_name* after a run if the policy demands it.

    Usage::

        with QuotaResetGuard(reset_policy, quota_policy, job_name) as g:
            g.set_success(result.exit_code == 0)
    """

    def __init__(
        self,
        reset_policy: QuotaResetPolicy,
        quota_policy: QuotaPolicy,
        job_name: str,
        log_dir: Optional[Path] = None,
    ) -> None:
        self._reset_policy = reset_policy
        self._quota_policy = quota_policy
        self._job_name = job_name
        self._log_dir = log_dir
        self._success: bool = False

    def set_success(self, value: bool) -> None:
        self._success = value

    def __enter__(self) -> "QuotaResetGuard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._reset_policy.enabled:
            return False
        if should_reset(self._reset_policy, self._job_name, self._success, self._log_dir):
            # Wipe the run-timestamps list so the quota counter starts fresh.
            state = load_quota_state(self._job_name, self._log_dir)
            state["runs"] = []
            save_quota_state(self._job_name, state, self._log_dir)
            record_reset(self._job_name, self._log_dir)
        return False
