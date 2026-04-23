"""Cascade policy: trigger downstream jobs when a job succeeds or fails."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CascadePolicy:
    """Defines downstream jobs to trigger based on job outcome."""

    on_success: List[str] = field(default_factory=list)
    on_failure: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.on_success, list):
            raise TypeError("on_success must be a list of job names")
        if not isinstance(self.on_failure, list):
            raise TypeError("on_failure must be a list of job names")
        for name in self.on_success:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("on_success entries must be non-empty strings")
        for name in self.on_failure:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("on_failure entries must be non-empty strings")
        self.on_success = [n.strip() for n in self.on_success]
        self.on_failure = [n.strip() for n in self.on_failure]

    @property
    def enabled(self) -> bool:
        return bool(self.on_success or self.on_failure)

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "CascadePolicy":
        if not cfg:
            return cls()
        return cls(
            on_success=cfg.get("on_success", []),
            on_failure=cfg.get("on_failure", []),
        )

    def jobs_for(self, success: bool) -> List[str]:
        """Return the list of downstream job names for the given outcome."""
        return self.on_success if success else self.on_failure
