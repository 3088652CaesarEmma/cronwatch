"""Context manager that fires healthcheck pings around a job execution.

Usage::

    policy = HealthcheckPolicy.from_config(job_cfg.get("healthcheck"))
    with HealthcheckGuard(policy, job_name="backup"):
        result = run_job(job)

On entry the /start ping is fired (if enabled).  On clean exit the success
ping is fired.  On exception the /fail ping is fired and the exception is
re-raised so the caller can still handle it.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Optional, Type

from cronwatch.healthcheck import HealthcheckPolicy, ping_start, ping_success, ping_failure

logger = logging.getLogger(__name__)


class HealthcheckGuard:
    """Fire healthcheck pings before and after a job block."""

    def __init__(self, policy: HealthcheckPolicy, job_name: str = "") -> None:
        self.policy = policy
        self.job_name = job_name

    def __enter__(self) -> "HealthcheckGuard":
        if self.policy.enabled and self.policy.ping_on_start:
            ok = ping_start(self.policy)
            if not ok:
                logger.warning(
                    "healthcheck start ping failed for job %r", self.job_name
                )
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if not self.policy.enabled:
            return False

        if exc_type is None:
            ok = ping_success(self.policy)
            if not ok:
                logger.warning(
                    "healthcheck success ping failed for job %r", self.job_name
                )
        else:
            ok = ping_failure(self.policy)
            if not ok:
                logger.warning(
                    "healthcheck failure ping failed for job %r", self.job_name
                )
        # Never suppress exceptions
        return False
