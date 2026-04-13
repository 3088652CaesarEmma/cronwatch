"""Label-based job grouping and filtering utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelPolicy:
    """Policy for label-based job grouping."""

    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.labels, dict):
            raise ValueError("labels must be a dict")
        for k, v in self.labels.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError("label keys and values must be strings")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "LabelPolicy":
        """Build a LabelPolicy from a config dict (or None)."""
        if not cfg:
            return cls()
        raw = cfg.get("labels", {})
        if not isinstance(raw, dict):
            raise ValueError("labels config must be a mapping")
        return cls(labels={str(k): str(v) for k, v in raw.items()})

    def get(self, key: str) -> Optional[str]:
        """Return the value for a label key, or None."""
        return self.labels.get(key)

    def matches(self, selector: Dict[str, str]) -> bool:
        """Return True if all selector key/value pairs are present in labels."""
        return all(self.labels.get(k) == v for k, v in selector.items())

    def enabled(self) -> bool:
        """Return True when at least one label is defined."""
        return bool(self.labels)


def filter_by_label_selector(
    jobs: List, selector: Dict[str, str]
) -> List:
    """Return jobs whose label policy matches all selector pairs.

    Each job is expected to have a ``label_policy`` attribute of type
    ``LabelPolicy``.  Jobs without the attribute are skipped.
    """
    result = []
    for job in jobs:
        policy: Optional[LabelPolicy] = getattr(job, "label_policy", None)
        if policy is not None and policy.matches(selector):
            result.append(job)
    return result


def collect_label_values(jobs: List, key: str) -> List[str]:
    """Collect unique values for a label key across all jobs."""
    seen: Dict[str, None] = {}
    for job in jobs:
        policy: Optional[LabelPolicy] = getattr(job, "label_policy", None)
        if policy is not None:
            val = policy.get(key)
            if val is not None and val not in seen:
                seen[val] = None
    return list(seen.keys())
