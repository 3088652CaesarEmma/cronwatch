"""Tests for cronwatch.quota_forecast."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cronwatch.quota import QuotaPolicy
from cronwatch.quota_forecast import ForecastResult, forecast_quota
from cronwatch.runcount import get_runcount_path, save_runcounts


@pytest.fixture()
def log_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed_counts(job_name: str, log_dir: str, timestamps: list[datetime]) -> None:
    path = get_runcount_path(job_name, log_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump([ts.isoformat() for ts in timestamps], fh)


def _disabled_policy() -> QuotaPolicy:
    return QuotaPolicy(max_runs=0, window_seconds=3600)


def _enabled_policy(max_runs: int = 10, window: int = 3600) -> QuotaPolicy:
    return QuotaPolicy(max_runs=max_runs, window_seconds=window)


# ---------------------------------------------------------------------------

def test_forecast_returns_none_when_policy_disabled(log_dir: str) -> None:
    result = forecast_quota("myjob", _disabled_policy(), log_dir)
    assert result is None


def test_forecast_no_runs_returns_zero_pct(log_dir: str) -> None:
    result = forecast_quota("myjob", _enabled_policy(), log_dir)
    assert result is not None
    assert result.current_count == 0
    assert result.pct_used == 0.0
    assert result.runs_remaining == 10
    assert result.projected_exhaustion is None
    assert not result.exhausted


def test_forecast_counts_only_within_window(log_dir: str) -> None:
    now = datetime.utcnow()
    old = now - timedelta(hours=2)
    recent = now - timedelta(minutes=5)
    _seed_counts("myjob", log_dir, [old, recent])
    result = forecast_quota("myjob", _enabled_policy(max_runs=10, window=3600), log_dir, now=now)
    assert result is not None
    assert result.current_count == 1


def test_forecast_exhausted_flag(log_dir: str) -> None:
    now = datetime.utcnow()
    timestamps = [now - timedelta(minutes=i) for i in range(10)]
    _seed_counts("myjob", log_dir, timestamps)
    result = forecast_quota("myjob", _enabled_policy(max_runs=10), log_dir, now=now)
    assert result is not None
    assert result.exhausted
    assert result.runs_remaining == 0
    assert "EXHAUSTED" in result.summary


def test_forecast_projects_exhaustion_with_steady_rate(log_dir: str) -> None:
    now = datetime.utcnow()
    # 5 runs evenly spaced over last 50 minutes => rate = 1 per 10 min
    timestamps = [now - timedelta(minutes=50 - i * 10) for i in range(5)]
    _seed_counts("myjob", log_dir, timestamps)
    result = forecast_quota("myjob", _enabled_policy(max_runs=10), log_dir, now=now)
    assert result is not None
    assert result.projected_exhaustion is not None
    assert result.projected_exhaustion > now


def test_forecast_summary_no_exhaustion(log_dir: str) -> None:
    result = forecast_quota("myjob", _enabled_policy(), log_dir)
    assert result is not None
    assert "no exhaustion projected" in result.summary


def test_forecast_result_pct_used(log_dir: str) -> None:
    now = datetime.utcnow()
    timestamps = [now - timedelta(minutes=i) for i in range(4)]
    _seed_counts("myjob", log_dir, timestamps)
    result = forecast_quota("myjob", _enabled_policy(max_runs=8), log_dir, now=now)
    assert result is not None
    assert abs(result.pct_used - 50.0) < 0.01


def test_forecast_single_run_no_projection(log_dir: str) -> None:
    now = datetime.utcnow()
    _seed_counts("myjob", log_dir, [now - timedelta(minutes=1)])
    result = forecast_quota("myjob", _enabled_policy(max_runs=10), log_dir, now=now)
    assert result is not None
    # Only 1 data point — cannot compute rate
    assert result.projected_exhaustion is None
