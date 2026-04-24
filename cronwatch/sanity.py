"""sanity.py — Pre-run sanity checks for cron jobs.

A SanityPolicy defines a list of shell commands that must all exit 0
before the job itself is allowed to run.  If any check fails the job
is skipped and a SanityCheckError is raised.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


class SanityCheckError(Exception):
    """Raised when a pre-run sanity check fails."""

    def __init__(self, job_name: str, check: str, exit_code: int) -> None:
        self.job_name = job_name
        self.check = check
        self.exit_code = exit_code
        super().__init__(
            f"Sanity check failed for '{job_name}': "
            f"command '{check}' exited with code {exit_code}"
        )


@dataclass
class SanityPolicy:
    checks: List[str] = field(default_factory=list)
    timeout: int = 10

    def __post_init__(self) -> None:
        if not isinstance(self.checks, list):
            raise TypeError("checks must be a list of strings")
        for item in self.checks:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("each sanity check must be a non-empty string")
        if self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")

    @property
    def enabled(self) -> bool:
        return bool(self.checks)

    @classmethod
    def from_config(cls, data: Optional[dict]) -> "SanityPolicy":
        if not data:
            return cls()
        return cls(
            checks=data.get("checks", []),
            timeout=int(data.get("timeout", 10)),
        )

    def run_checks(self, job_name: str) -> None:
        """Execute every check command; raise SanityCheckError on first failure."""
        for check in self.checks:
            try:
                result = subprocess.run(
                    check,
                    shell=True,
                    timeout=self.timeout,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode != 0:
                    raise SanityCheckError(job_name, check, result.returncode)
            except subprocess.TimeoutExpired:
                raise SanityCheckError(job_name, check, -1)
