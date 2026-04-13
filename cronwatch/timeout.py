"""Timeout enforcement for cron job execution."""

from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Optional


class JobTimeoutError(Exception):
    """Raised when a job exceeds its allowed execution time."""

    def __init__(self, seconds: int) -> None:
        self.seconds = seconds
        super().__init__(f"Job timed out after {seconds} second(s)")


@dataclass
class TimeoutPolicy:
    """Defines how long a job is allowed to run before being killed."""

    seconds: Optional[int] = None
    kill_on_timeout: bool = True

    def __post_init__(self) -> None:
        if self.seconds is not None and self.seconds <= 0:
            raise ValueError("timeout seconds must be a positive integer")

    @property
    def enabled(self) -> bool:
        return self.seconds is not None

    @classmethod
    def from_config(cls, cfg: dict) -> "TimeoutPolicy":
        """Build a TimeoutPolicy from a job config dict."""
        seconds = cfg.get("timeout")
        kill = cfg.get("kill_on_timeout", True)
        return cls(seconds=seconds, kill_on_timeout=kill)


def _timeout_handler(signum: int, frame: object) -> None:  # noqa: ARG001
    raise JobTimeoutError(0)  # seconds filled in by enforce_timeout


class enforce_timeout:  # noqa: N801  (context manager, lowercase intentional)
    """Context manager that raises JobTimeoutError if block exceeds *seconds*.

    Only functional on UNIX systems (requires SIGALRM).
    """

    def __init__(self, policy: TimeoutPolicy) -> None:
        self.policy = policy
        self._old_handler = None

    def __enter__(self) -> "enforce_timeout":
        if self.policy.enabled and hasattr(signal, "SIGALRM"):
            self._old_handler = signal.signal(signal.SIGALRM, self._handler)
            signal.alarm(self.policy.seconds)  # type: ignore[arg-type]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.policy.enabled and hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)
        if isinstance(exc_val, JobTimeoutError):
            exc_val.seconds = self.policy.seconds  # type: ignore[assignment]
        return False

    def _handler(self, signum: int, frame: object) -> None:
        raise JobTimeoutError(self.policy.seconds or 0)
