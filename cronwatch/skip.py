"""Skip policy: conditionally skip job execution based on an exit-code check.

If a `skip_if` shell command is configured and exits with code 0, the job
is skipped for the current run.  This is useful for guarding jobs behind
condition checks (e.g. skip a backup job if the target mount is absent).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Optional


class JobSkippedError(Exception):
    """Raised by SkipGuard when the skip condition is satisfied."""

    def __init__(self, job_name: str, reason: str) -> None:
        self.job_name = job_name
        self.reason = reason
        super().__init__(f"Job '{job_name}' skipped: {reason}")


@dataclass
class SkipPolicy:
    """Policy controlling conditional skip behaviour for a job."""

    skip_if: Optional[str] = None          # shell command whose exit-0 triggers skip
    timeout: int = 10                       # seconds to wait for the skip_if command
    shell: bool = True

    def __post_init__(self) -> None:
        if self.skip_if is not None and not isinstance(self.skip_if, str):
            raise TypeError("skip_if must be a string or None")
        if self.skip_if == "":
            self.skip_if = None
        if not isinstance(self.timeout, int) or self.timeout < 1:
            raise ValueError("timeout must be a positive integer")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SkipPolicy":
        if not cfg:
            return cls()
        return cls(
            skip_if=cfg.get("skip_if"),
            timeout=int(cfg.get("timeout", 10)),
            shell=bool(cfg.get("shell", True)),
        )

    @property
    def enabled(self) -> bool:
        return self.skip_if is not None

    def should_skip(self) -> bool:
        """Return True if the skip condition exits with code 0."""
        if not self.enabled:
            return False
        try:
            result = subprocess.run(
                self.skip_if,
                shell=self.shell,
                timeout=self.timeout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
