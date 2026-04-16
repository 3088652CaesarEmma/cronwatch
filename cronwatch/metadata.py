"""Job metadata attachment and retrieval."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MetadataPolicy:
    """Arbitrary key/value metadata attached to a job."""

    labels: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.labels, dict):
            raise TypeError("metadata labels must be a dict")
        for k in self.labels:
            if not isinstance(k, str) or not k.strip():
                raise ValueError(f"metadata key must be a non-empty string, got {k!r}")

    @classmethod
    def from_config(cls, cfg: Optional[Dict[str, Any]]) -> "MetadataPolicy":
        if not cfg:
            return cls()
        labels = cfg.get("labels", {})
        if not isinstance(labels, dict):
            raise TypeError("metadata.labels must be a mapping")
        return cls(labels=labels)

    def get(self, key: str, default: Any = None) -> Any:
        """Return value for *key* or *default* if absent."""
        return self.labels.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value*."""
        if not isinstance(key, str) or not key.strip():
            raise ValueError("metadata key must be a non-empty string")
        self.labels[key] = value

    def merge(self, other: "MetadataPolicy") -> "MetadataPolicy":
        """Return a new policy with labels from both, *other* wins on conflict."""
        merged = {**self.labels, **other.labels}
        return MetadataPolicy(labels=merged)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.labels)

    def enabled(self) -> bool:
        return bool(self.labels)
