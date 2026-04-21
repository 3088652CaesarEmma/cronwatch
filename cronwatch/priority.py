"""Job priority policy — assigns and compares execution priorities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

DEFAULT_PRIORITY = 50
_MIN_PRIORITY = 0
_MAX_PRIORITY = 100


@dataclass
class PriorityPolicy:
    """Assigns a numeric priority (0=lowest, 100=highest) to a job."""

    priority: int = DEFAULT_PRIORITY

    def __post_init__(self) -> None:
        if not isinstance(self.priority, int):
            raise TypeError(
                f"priority must be an int, got {type(self.priority).__name__}"
            )
        if not (_MIN_PRIORITY <= self.priority <= _MAX_PRIORITY):
            raise ValueError(
                f"priority must be between {_MIN_PRIORITY} and {_MAX_PRIORITY}, "
                f"got {self.priority}"
            )

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "PriorityPolicy":
        """Build a PriorityPolicy from a config dict (or None for defaults)."""
        if not cfg:
            return cls()
        return cls(priority=int(cfg.get("priority", DEFAULT_PRIORITY)))

    @property
    def enabled(self) -> bool:
        """True when priority differs from the default (scheduling hint active)."""
        return self.priority != DEFAULT_PRIORITY

    def is_higher_than(self, other: "PriorityPolicy") -> bool:
        """Return True if this policy has a strictly higher priority."""
        return self.priority > other.priority

    def is_lower_than(self, other: "PriorityPolicy") -> bool:
        """Return True if this policy has a strictly lower priority."""
        return self.priority < other.priority


def sort_jobs_by_priority(jobs: list, *, reverse: bool = False) -> list:
    """Return *jobs* sorted by their ``priority`` attribute (highest first by default).

    Jobs without a ``priority`` attribute are treated as DEFAULT_PRIORITY.
    """
    def _key(job):
        policy = getattr(job, "priority", None)
        if isinstance(policy, PriorityPolicy):
            return policy.priority
        if isinstance(policy, int):
            return policy
        return DEFAULT_PRIORITY

    return sorted(jobs, key=_key, reverse=not reverse)
