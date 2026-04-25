"""Context manager that enforces pre-flight checks before job execution."""
from __future__ import annotations

from cronwatch.precheck import PrecheckPolicy


class PrecheckGuard:
    """Run pre-flight checks on entry; propagate any PrecheckFailedError."""

    def __init__(self, policy: PrecheckPolicy, job_name: str) -> None:
        self._policy = policy
        self._job_name = job_name

    def __enter__(self) -> "PrecheckGuard":
        self._policy.run(self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:  # type: ignore[override]
        return False
