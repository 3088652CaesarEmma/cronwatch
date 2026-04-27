"""Tests for cronwatch.quota_rollover_guard."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.quota import load_quota_state, save_quota_state
from cronwatch.quota_rollover import QuotaRolloverPolicy, save_rollover_state
from cronwatch.quota_rollover_guard import QuotaRolloverGuard


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed_quota(job_name: str, log_dir: Path, count: int) -> None:
    now = 1_700_000_000.0
    runs = [now + i for i in range(count)]
    save_quota_state(job_name, runs, log_dir)


def test_guard_disabled_policy_does_not_reset(log_dir: Path):
    _seed_quota("myjob", log_dir, 3)
    policy = QuotaRolloverPolicy()  # disabled
    with QuotaRolloverGuard("myjob", policy, log_dir) as g:
        pass
    assert not g.rolled_over
    assert len(load_quota_state("myjob", log_dir)) == 3


def test_guard_resets_quota_on_rollover(log_dir: Path):
    _seed_quota("myjob", log_dir, 5)
    # Force stale bucket so rollover fires
    save_rollover_state("myjob", {"bucket": "1999-001"}, log_dir)
    policy = QuotaRolloverPolicy(period="daily")
    with QuotaRolloverGuard("myjob", policy, log_dir) as g:
        pass
    assert g.rolled_over
    assert load_quota_state("myjob", log_dir) == []


def test_guard_no_rollover_when_same_bucket(log_dir: Path):
    _seed_quota("myjob", log_dir, 2)
    policy = QuotaRolloverPolicy(period="daily")
    # Prime the bucket so it matches current period
    with QuotaRolloverGuard("myjob", policy, log_dir):
        pass
    _seed_quota("myjob", log_dir, 2)  # re-seed after first guard primed it
    with QuotaRolloverGuard("myjob", policy, log_dir) as g:
        pass
    assert not g.rolled_over
    assert len(load_quota_state("myjob", log_dir)) == 2


def test_guard_does_not_suppress_exceptions(log_dir: Path):
    policy = QuotaRolloverPolicy(period="daily")
    with pytest.raises(RuntimeError):
        with QuotaRolloverGuard("myjob", policy, log_dir):
            raise RuntimeError("boom")


def test_guard_returns_self_on_enter(log_dir: Path):
    policy = QuotaRolloverPolicy()
    g = QuotaRolloverGuard("myjob", policy, log_dir)
    result = g.__enter__()
    assert result is g
    g.__exit__(None, None, None)
