"""quota_budget.py — Combined quota + budget enforcement guard.

Runs a job only if it is within both its run-count quota and its
runtime-seconds budget for the current window.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwatch.quota import QuotaPolicy, QuotaExceededError  # type: ignore
from cronwatch.budget import BudgetPolicy  # type: ignore
from cronwatch.quota_guard import QuotaGuard  # type: ignore


class BudgetExceededError(Exception):
    """Raised when a job has consumed its allowed runtime budget."""

    def __init__(self, job_name: str, used: float, limit: float) -> None:
        self.job_name = job_name
        self.used = used
        self.limit = limit
        super().__init__(
            f"Job '{job_name}' budget exceeded: {used:.1f}s used of {limit:.1f}s allowed."
        )


@dataclass
class QuotaBudgetGuard:
    """Context manager that enforces both quota and budget policies.

    Parameters
    ----------
    job_name:
        Logical name of the cron job.
    quota_policy:
        :class:`QuotaPolicy` instance (may be disabled).
    budget_policy:
        :class:`BudgetPolicy` instance (may be disabled).
    log_dir:
        Directory used to persist state files.
    """

    job_name: str
    quota_policy: QuotaPolicy
    budget_policy: BudgetPolicy
    log_dir: str
    _quota_guard: Optional[QuotaGuard] = field(default=None, init=False, repr=False)

    def __enter__(self) -> "QuotaBudgetGuard":
        # --- quota check ---
        if self.quota_policy.enabled:
            self._quota_guard = QuotaGuard(
                self.job_name, self.quota_policy, self.log_dir
            )
            self._quota_guard.__enter__()

        # --- budget check ---
        if self.budget_policy.enabled:
            used = self.budget_policy.get_used_seconds(self.job_name, self.log_dir)
            limit = self.budget_policy.max_seconds
            if used >= limit:
                raise BudgetExceededError(self.job_name, used, limit)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._quota_guard is not None:
            self._quota_guard.__exit__(exc_type, exc_val, exc_tb)
        return False
