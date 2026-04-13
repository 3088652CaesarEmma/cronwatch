"""Output truncation utilities for cronwatch.

Provides helpers to truncate captured stdout/stderr before logging
or sending notifications, respecting configurable byte/line limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


_DEFAULT_MAX_LINES = 100
_DEFAULT_MAX_BYTES = 16_384  # 16 KiB


@dataclass
class TruncatePolicy:
    """Policy controlling how long output is truncated."""

    max_lines: int = _DEFAULT_MAX_LINES
    max_bytes: int = _DEFAULT_MAX_BYTES
    marker: str = "... (truncated)"

    def __post_init__(self) -> None:
        if self.max_lines < 1:
            raise ValueError("max_lines must be >= 1")
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be >= 1")

    @classmethod
    def from_config(cls, cfg: dict) -> "TruncatePolicy":
        """Build a TruncatePolicy from a config mapping."""
        return cls(
            max_lines=int(cfg.get("max_lines", _DEFAULT_MAX_LINES)),
            max_bytes=int(cfg.get("max_bytes", _DEFAULT_MAX_BYTES)),
            marker=str(cfg.get("marker", "... (truncated)")),
        )

    @property
    def enabled(self) -> bool:
        return True


def truncate_output(text: str, policy: Optional[TruncatePolicy] = None) -> str:
    """Truncate *text* according to *policy*.

    Applies line-count limit first, then byte limit.  If either limit
    is exceeded the truncation marker is appended on its own line.

    Args:
        text: The raw captured output string.
        policy: Truncation policy; uses defaults when *None*.

    Returns:
        Possibly-truncated string.
    """
    if policy is None:
        policy = TruncatePolicy()

    lines = text.splitlines(keepends=True)
    truncated = False

    if len(lines) > policy.max_lines:
        lines = lines[: policy.max_lines]
        truncated = True

    result = "".join(lines)

    if len(result.encode()) > policy.max_bytes:
        encoded = result.encode()
        result = encoded[: policy.max_bytes].decode(errors="ignore")
        truncated = True

    if truncated:
        result = result.rstrip("\n") + "\n" + policy.marker

    return result
