"""Quota usage forecasting: project future quota exhaustion based on historical run counts."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from cronwatch.quota import QuotaPolicy
from cronwatch.runcount import load_runcounts


@dataclass
class ForecastResult:
    job_name: str
    window_seconds: int
    max_runs: int
    current_count: int
    runs_remaining: int
    pct_used: float
    projected_exhaustion: Optional[datetime]
    exhausted: bool = field(init=False)

    def __post_init__(self) -> None:
        self.exhausted = self.current_count >= self.max_runs

    @property
    def summary(self) -> str:
        if self.exhausted:
            return f"{self.job_name}: quota EXHAUSTED ({self.current_count}/{self.max_runs})"
        if self.projected_exhaustion is None:
            return f"{self.job_name}: {self.pct_used:.1f}% used, no exhaustion projected"
        ts = self.projected_exhaustion.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{self.job_name}: {self.pct_used:.1f}% used, "
            f"projected exhaustion at {ts}"
        )


def forecast_quota(
    job_name: str,
    policy: QuotaPolicy,
    log_dir: str,
    now: Optional[datetime] = None,
) -> Optional[ForecastResult]:
    """Return a ForecastResult for *job_name* or None if policy is disabled."""
    if not policy.enabled:
        return None

    if now is None:
        now = datetime.utcnow()

    counts = load_runcounts(job_name, log_dir)
    window_start = now - timedelta(seconds=policy.window_seconds)
    recent = [ts for ts in counts if ts >= window_start]
    current_count = len(recent)
    runs_remaining = max(0, policy.max_runs - current_count)
    pct_used = (current_count / policy.max_runs) * 100.0 if policy.max_runs > 0 else 0.0

    projected_exhaustion: Optional[datetime] = None
    if current_count >= 2 and current_count < policy.max_runs:
        sorted_recent = sorted(recent)
        elapsed = (sorted_recent[-1] - sorted_recent[0]).total_seconds()
        if elapsed > 0:
            rate = current_count / elapsed  # runs per second
            seconds_to_exhaust = runs_remaining / rate
            if not math.isinf(seconds_to_exhaust):
                projected_exhaustion = now + timedelta(seconds=seconds_to_exhaust)

    return ForecastResult(
        job_name=job_name,
        window_seconds=policy.window_seconds,
        max_runs=policy.max_runs,
        current_count=current_count,
        runs_remaining=runs_remaining,
        pct_used=pct_used,
        projected_exhaustion=projected_exhaustion,
    )
