"""Context manager that updates watermarks after a job completes."""
from __future__ import annotations

from typing import Optional

from cronwatch.watermark import WatermarkPolicy, update_watermarks
from cronwatch.runner import JobResult


class WatermarkGuard:
    """Records high-watermark stats for a job after it finishes.

    Usage::

        with WatermarkGuard(policy, log_dir=log_dir) as guard:
            result = run_job(command)
            guard.set_result(result)
    """

    def __init__(self, policy: WatermarkPolicy, log_dir: Optional[str] = None) -> None:
        self._policy = policy
        self._log_dir = log_dir
        self._result: Optional[JobResult] = None

    def __enter__(self) -> "WatermarkGuard":
        return self

    def set_result(self, result: JobResult) -> None:
        self._result = result

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._result is not None and self._policy.enabled:
            update_watermarks(self._result, self._policy, self._log_dir)
        return False
