"""Guard that enforces TagRulePolicy before running a job."""

from __future__ import annotations

from typing import List

from cronwatch.tagrule import TagRulePolicy


class TagRuleViolationError(Exception):
    """Raised when a job's tags do not satisfy the active TagRulePolicy."""

    def __init__(self, job_name: str, tags: List[str], policy: TagRulePolicy) -> None:
        self.job_name = job_name
        self.tags = tags
        self.policy = policy
        super().__init__(
            f"Job '{job_name}' with tags {tags} does not satisfy tag rule policy "
            f"(require_any={policy.require_any}, require_all={policy.require_all}, "
            f"exclude={policy.exclude})"
        )


class TagRuleGuard:
    """Context manager that blocks execution when tag rules are not satisfied."""

    def __init__(self, job_name: str, tags: List[str], policy: TagRulePolicy) -> None:
        self.job_name = job_name
        self.tags = tags
        self.policy = policy

    def __enter__(self) -> "TagRuleGuard":
        if self.policy.enabled() and not self.policy.matches(self.tags):
            raise TagRuleViolationError(self.job_name, self.tags, self.policy)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
