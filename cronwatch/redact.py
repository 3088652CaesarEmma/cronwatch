"""Output redaction for sensitive values in job output and logs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


_DEFAULT_PATTERNS = [
    r"(?i)password=[^\s&]+",
    r"(?i)token=[^\s&]+",
    r"(?i)secret=[^\s&]+",
    r"(?i)api[_-]?key=[^\s&]+",
]

REDACTED = "[REDACTED]"


@dataclass
class RedactPolicy:
    """Policy controlling which patterns are redacted from job output."""

    patterns: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.patterns, list):
            raise TypeError("patterns must be a list of strings")
        self._compiled: List[re.Pattern] = [
            re.compile(p) for p in (_DEFAULT_PATTERNS + self.patterns)
        ]

    @classmethod
    def from_config(cls, cfg: dict) -> "RedactPolicy":
        """Build a RedactPolicy from a config dict section."""
        redact_cfg = cfg.get("redact", {})
        return cls(
            patterns=redact_cfg.get("patterns", []),
            enabled=redact_cfg.get("enabled", True),
        )

    def redact(self, text: str) -> str:
        """Return *text* with all sensitive patterns replaced by REDACTED."""
        if not self.enabled or not text:
            return text
        result = text
        for pattern in self._compiled:
            result = pattern.sub(REDACTED, result)
        return result
