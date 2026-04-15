"""Tag-based rule evaluation for conditional job execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class TagRulePolicy:
    """Policy that controls job execution based on tag inclusion/exclusion rules."""

    require_any: List[str] = field(default_factory=list)
    require_all: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for attr in ("require_any", "require_all", "exclude"):
            val = getattr(self, attr)
            if not isinstance(val, list):
                raise TypeError(f"{attr} must be a list, got {type(val).__name__}")
            for item in val:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(f"{attr} entries must be non-empty strings")
        cleaned = [t.strip() for t in self.require_any]
        self.require_any = cleaned
        self.require_all = [t.strip() for t in self.require_all]
        self.exclude = [t.strip() for t in self.exclude]

    @classmethod
    def from_config(cls, cfg: dict | None) -> "TagRulePolicy":
        if not cfg:
            return cls()
        return cls(
            require_any=cfg.get("require_any", []),
            require_all=cfg.get("require_all", []),
            exclude=cfg.get("exclude", []),
        )

    def enabled(self) -> bool:
        return bool(self.require_any or self.require_all or self.exclude)

    def matches(self, tags: List[str]) -> bool:
        """Return True if the given tag set satisfies this rule policy."""
        tag_set: Set[str] = set(tags)

        if self.exclude and tag_set & set(self.exclude):
            return False

        if self.require_all and not set(self.require_all).issubset(tag_set):
            return False

        if self.require_any and not tag_set & set(self.require_any):
            return False

        return True
