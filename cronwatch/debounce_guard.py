"""Context manager that enforces the debounce policy around notifications."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwatch.debounce import DebouncePolicy, record_fired, should_debounce


class DebounceGuard:
    """Wrap a notification call; skip it when the job is within its debounce window."""

    def __init__(
        self,
        policy: DebouncePolicy,
        job_name: str,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.policy = policy
        self.job_name = job_name
        self.log_dir = log_dir
        self.suppressed: bool = False

    def __enter__(self) -> "DebounceGuard":
        if should_debounce(self.policy, self.job_name, self.log_dir):
            self.suppressed = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self.suppressed and exc_type is None:
            # Notification was sent successfully — record the timestamp.
            record_fired(self.job_name, self.log_dir)
        return False  # never suppress exceptions
