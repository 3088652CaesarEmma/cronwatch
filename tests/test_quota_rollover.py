"""Tests for cronwatch.quota_rollover."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.quota_rollover import (
    QuotaRolloverPolicy,
    _period_bucket,
    get_rollover_state_path,
    load_rollover_state,
    maybe_rollover,
    save_rollover_state,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- Policy ---

def test_quota_rollover_policy_defaults():
    p = QuotaRolloverPolicy()
    assert p.period is None
    assert not p.enabled


def test_quota_rollover_policy_valid_periods():
    for period in ("hourly", "daily", "weekly", "monthly"):
        p = QuotaRolloverPolicy(period=period)
        assert p.period == period
        assert p.enabled


def test_quota_rollover_policy_invalid_period_raises():
    with pytest.raises(ValueError):
        QuotaRolloverPolicy(period="yearly")


def test_quota_rollover_policy_strips_whitespace():
    p = QuotaRolloverPolicy(period="  daily  ")
    assert p.period == "daily"


def test_quota_rollover_policy_invalid_type_raises():
    with pytest.raises(TypeError):
        QuotaRolloverPolicy(period=7)  # type: ignore[arg-type]


def test_from_config_none_returns_defaults():
    p = QuotaRolloverPolicy.from_config(None)
    assert p.period is None


def test_from_config_sets_period():
    p = QuotaRolloverPolicy.from_config({"period": "weekly"})
    assert p.period == "weekly"


# --- State helpers ---

def test_get_rollover_state_path_uses_log_dir(log_dir: Path):
    path = get_rollover_state_path("myjob", log_dir)
    assert str(log_dir) in str(path)
    assert "myjob" in str(path)


def test_save_and_load_roundtrip(log_dir: Path):
    save_rollover_state("myjob", {"bucket": "2024-001"}, log_dir)
    state = load_rollover_state("myjob", log_dir)
    assert state["bucket"] == "2024-001"


def test_load_returns_empty_when_no_file(log_dir: Path):
    state = load_rollover_state("nonexistent", log_dir)
    assert state == {}


# --- Period bucket ---

def test_period_bucket_daily_format():
    bucket = _period_bucket("daily")
    assert "-" in bucket


def test_period_bucket_weekly_contains_W():
    bucket = _period_bucket("weekly")
    assert "W" in bucket


# --- maybe_rollover ---

def test_maybe_rollover_disabled_policy_returns_false(log_dir: Path):
    policy = QuotaRolloverPolicy()
    assert maybe_rollover("myjob", policy, log_dir) is False


def test_maybe_rollover_first_run_returns_true(log_dir: Path):
    policy = QuotaRolloverPolicy(period="daily")
    assert maybe_rollover("myjob", policy, log_dir) is True


def test_maybe_rollover_same_bucket_returns_false(log_dir: Path):
    policy = QuotaRolloverPolicy(period="daily")
    maybe_rollover("myjob", policy, log_dir)  # first call sets bucket
    assert maybe_rollover("myjob", policy, log_dir) is False


def test_maybe_rollover_new_bucket_returns_true(log_dir: Path):
    policy = QuotaRolloverPolicy(period="daily")
    save_rollover_state("myjob", {"bucket": "1999-001"}, log_dir)
    assert maybe_rollover("myjob", policy, log_dir) is True
