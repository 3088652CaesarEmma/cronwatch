"""Dry-run support: skip actual execution and report what would have run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwatch.runner import JobResult


@dataclass
class DryRunPolicy:
    """Policy controlling dry-run behaviour."""

    enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")

    @classmethod
    def from_config(cls, cfg: dict | None) -> "DryRunPolicy":
        if not cfg:
            return cls()
        return cls(enabled=bool(cfg.get("enabled", False)))


@dataclass
class DryRunRecorder:
    """Collects the jobs that would have been executed in a dry run."""

    _entries: List[str] = field(default_factory=list, init=False)

    def record(self, command: str) -> None:
        """Record a command that was skipped."""
        self._entries.append(command)

    def recorded(self) -> List[str]:
        """Return a copy of all recorded commands."""
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()


def make_dry_run_result(command: str) -> JobResult:
    """Return a fake successful JobResult without running the command."""
    return JobResult(
        command=command,
        exit_code=0,
        stdout="[dry-run] command not executed",
        stderr="",
        duration=0.0,
    )
