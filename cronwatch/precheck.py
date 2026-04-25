"""Pre-flight checks that must pass before a job is allowed to run."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


class PrecheckFailedError(Exception):
    """Raised when one or more pre-flight checks fail."""

    def __init__(self, job_name: str, failed: List[str]) -> None:
        self.job_name = job_name
        self.failed = failed
        checks = ", ".join(repr(c) for c in failed)
        super().__init__(f"Pre-flight checks failed for '{job_name}': {checks}")


@dataclass
class PrecheckPolicy:
    """Policy controlling pre-flight shell checks for a job."""

    checks: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.checks, list):
            raise TypeError("checks must be a list of shell command strings")
        for item in self.checks:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("each check must be a non-empty string")
        self.checks = [c.strip() for c in self.checks]

    @property
    def enabled(self) -> bool:
        return bool(self.checks)

    @classmethod
    def from_config(cls, data: Optional[dict]) -> "PrecheckPolicy":
        if not data:
            return cls()
        return cls(checks=data.get("checks", []))

    def run(self, job_name: str) -> None:
        """Execute all checks; raise PrecheckFailedError if any fail."""
        if not self.enabled:
            return
        failed: List[str] = []
        for cmd in self.checks:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode != 0:
                    failed.append(cmd)
            except Exception:
                failed.append(cmd)
        if failed:
            raise PrecheckFailedError(job_name, failed)
