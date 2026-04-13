"""Output capture and processing pipeline for cron job results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwatch.truncate import TruncatePolicy
from cronwatch.redact import RedactPolicy


@dataclass
class OutputPolicy:
    """Combined policy for processing captured job output."""

    truncate: TruncatePolicy = field(default_factory=TruncatePolicy)
    redact: RedactPolicy = field(default_factory=RedactPolicy)

    @classmethod
    def from_config(cls, cfg: dict) -> "OutputPolicy":
        """Build an OutputPolicy from a raw config dict."""
        return cls(
            truncate=TruncatePolicy.from_config(cfg.get("truncate", {})),
            redact=RedactPolicy.from_config(cfg.get("redact", {})),
        )


def process_output(raw: Optional[str], policy: OutputPolicy) -> str:
    """Apply truncation and redaction to raw captured output.

    Args:
        raw: Raw stdout or stderr string, or None.
        policy: OutputPolicy describing how to process the text.

    Returns:
        Processed output string (never None).
    """
    text = raw or ""

    if policy.truncate.enabled:
        text = policy.truncate.truncate_output(text)

    if policy.redact.patterns:
        text = policy.redact.redact(text)

    return text


def process_result_output(stdout: Optional[str], stderr: Optional[str],
                          policy: OutputPolicy) -> tuple[str, str]:
    """Process both stdout and stderr through the output policy.

    Args:
        stdout: Captured stdout string.
        stderr: Captured stderr string.
        policy: OutputPolicy to apply.

    Returns:
        Tuple of (processed_stdout, processed_stderr).
    """
    return (
        process_output(stdout, policy),
        process_output(stderr, policy),
    )
