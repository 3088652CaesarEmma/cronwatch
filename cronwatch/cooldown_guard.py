"""Context manager guard that enforces cooldown policy before running a job."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwatch.cooldown import CooldownPolicy, is_cooling_down


class CooldownActiveError(Exception):
    """Raised when a job is attempted during its cooldown window."""

    def __init__(self, job_name: str, seconds_remaining: float) -> None:
        self.job_name = job_name
        self.seconds_remaining = seconds_remaining
        super().__init__(
            f"Job '{job_name}' is in cooldown for another "
            f"{seconds_remaining:.1f}s after a previous failure."
        )


class CooldownGuard:
    """Raises CooldownActiveError on __enter__ if the job is cooling down."""

    def __init__(
        self,
        job_name: str,
        policy: CooldownPolicy,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.job_name = job_name
        self.policy = policy
        self.log_dir = log_dir

    def __enter__(self) -> "CooldownGuard":
        if not self.policy.enabled:
            return self
        from cronwatch.cooldown import load_cooldown_state
        import time

        state = load_cooldown_state(self.job_name, self.log_dir)
        last_failure = state.get("last_failure")
        if last_failure is not None:
            elapsed = time.time() - last_failure
            if elapsed < self.policy.seconds:
                remaining = self.policy.seconds - elapsed
                raise CooldownActiveError(self.job_name, remaining)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
