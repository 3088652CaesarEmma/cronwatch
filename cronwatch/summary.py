"""RunSummary: aggregate multiple JobResult objects into a report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwatch.runner import JobResult


@dataclass
class RunSummary:
    results: List[JobResult] = field(default_factory=list)

    def add(self, result: JobResult) -> None:
        self.results.append(result)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.exit_code == 0)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.exit_code != 0)

    @property
    def success_count(self) -> int:
        return self.succeeded

    @property
    def failure_count(self) -> int:
        return self.failed

    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.succeeded / self.total

    def failed_results(self) -> List[JobResult]:
        return [r for r in self.results if r.exit_code != 0]

    def succeeded_results(self) -> List[JobResult]:
        return [r for r in self.results if r.exit_code == 0]

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "success_rate": self.success_rate(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RunSummary(total={self.total}, "
            f"succeeded={self.succeeded}, failed={self.failed})"
        )
