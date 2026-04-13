"""Summary report generation for cronwatch job runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwatch.runner import JobResult


@dataclass
class RunSummary:
    """Aggregated summary of one or more job results."""

    results: List[JobResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> List[JobResult]:
        return [r for r in self.results if r.exit_code == 0]

    @property
    def failed(self) -> List[JobResult]:
        return [r for r in self.results if r.exit_code != 0]

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    @property
    def all_passed(self) -> bool:
        return self.failure_count == 0 and self.total > 0

    def add(self, result: JobResult) -> None:
        """Append a job result to the summary."""
        self.results.append(result)

    def as_text(self) -> str:
        """Render a human-readable summary report."""
        lines = [
            "=== Cronwatch Run Summary ===",
            f"Total jobs : {self.total}",
            f"Succeeded  : {self.success_count}",
            f"Failed     : {self.failure_count}",
        ]
        if self.failed:
            lines.append("\nFailed jobs:")
            for r in self.failed:
                lines.append(f"  - {r.command}  (exit {r.exit_code})")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        """Return a serialisable dict representation."""
        return {
            "total": self.total,
            "succeeded": self.success_count,
            "failed": self.failure_count,
            "all_passed": self.all_passed,
            "failed_jobs": [
                {"command": r.command, "exit_code": r.exit_code}
                for r in self.failed
            ],
        }
