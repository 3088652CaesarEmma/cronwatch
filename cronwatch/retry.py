"""Retry logic for cron job execution."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from cronwatch.runner import JobResult, run_job


@dataclass
class RetryPolicy:
    """Defines how retries should be attempted for a failed job."""

    max_attempts: int = 1
    delay_seconds: float = 5.0
    backoff_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")

    def delay_for(self, attempt: int) -> float:
        """Return the delay in seconds before the given attempt (0-indexed)."""
        if attempt == 0:
            return 0.0
        return self.delay_seconds * (self.backoff_factor ** (attempt - 1))


@dataclass
class RetryResult:
    """Outcome of a run_with_retry call."""

    attempts: int
    results: list[JobResult] = field(default_factory=list)

    @property
    def final(self) -> JobResult:
        return self.results[-1]

    @property
    def succeeded(self) -> bool:
        return self.final.exit_code == 0


def run_with_retry(
    command: str,
    policy: RetryPolicy,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Run *command* up to policy.max_attempts times, stopping on success."""
    results: list[JobResult] = []

    for attempt in range(policy.max_attempts):
        delay = policy.delay_for(attempt)
        if delay > 0:
            sleep_fn(delay)

        result = run_job(command)
        results.append(result)

        if result.exit_code == 0:
            break

    return RetryResult(attempts=len(results), results=results)


def policy_from_config(job_cfg: dict) -> RetryPolicy:
    """Build a RetryPolicy from a job config dict (keys: retry_attempts, retry_delay, retry_backoff)."""
    return RetryPolicy(
        max_attempts=int(job_cfg.get("retry_attempts", 1)),
        delay_seconds=float(job_cfg.get("retry_delay", 5.0)),
        backoff_factor=float(job_cfg.get("retry_backoff", 1.0)),
    )
