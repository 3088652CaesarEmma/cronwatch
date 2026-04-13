"""Tests for cronwatch.quota."""

import json
import time
from pathlib import Path

import pytest

from cronwatch.quota import (
    QuotaPolicy,
    check_quota,
    get_quota_state_path,
    record_quota_run,
)


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


# --- QuotaPolicy unit tests ---

def test_quota_policy_defaults():
    p = QuotaPolicy()
    assert p.max_runs == 0
    assert p.window_seconds == 3600
    assert not p.enabled


def test_quota_policy_enabled_when_nonzero():
    p = QuotaPolicy(max_runs=5)
    assert p.enabled


def test_quota_policy_negative_max_runs_raises():
    with pytest.raises(ValueError, match="max_runs"):
        QuotaPolicy(max_runs=-1)


def test_quota_policy_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        QuotaPolicy(max_runs=1, window_seconds=0)


def test_quota_policy_from_config_none_returns_defaults():
    p = QuotaPolicy.from_config(None)
    assert p.max_runs == 0


def test_quota_policy_from_config_values():
    p = QuotaPolicy.from_config({"max_runs": 10, "window_seconds": 7200})
    assert p.max_runs == 10
    assert p.window_seconds == 7200


# --- State path ---

def test_get_quota_state_path_uses_log_dir(log_dir):
    path = get_quota_state_path(log_dir, "backup")
    assert str(path).startswith(log_dir)
    assert path.suffix == ".json"
    assert "backup" in path.name


def test_get_quota_state_path_sanitises_name(log_dir):
    path = get_quota_state_path(log_dir, "my job")
    assert " " not in path.name


# --- check_quota / record_quota_run ---

def test_check_quota_disabled_always_allows(log_dir):
    p = QuotaPolicy(max_runs=0)
    assert check_quota(p, log_dir, "job") is True


def test_check_quota_allows_when_under_limit(log_dir):
    p = QuotaPolicy(max_runs=3, window_seconds=3600)
    assert check_quota(p, log_dir, "job") is True


def test_check_quota_blocks_when_limit_reached(log_dir):
    p = QuotaPolicy(max_runs=2, window_seconds=3600)
    record_quota_run(p, log_dir, "job")
    record_quota_run(p, log_dir, "job")
    assert check_quota(p, log_dir, "job") is False


def test_check_quota_ignores_expired_timestamps(log_dir):
    p = QuotaPolicy(max_runs=2, window_seconds=60)
    path = get_quota_state_path(log_dir, "job")
    path.parent.mkdir(parents=True, exist_ok=True)
    old_ts = time.time() - 120  # outside the 60-second window
    path.write_text(json.dumps({"runs": [old_ts, old_ts]}))
    # Both timestamps are expired, so quota should be free
    assert check_quota(p, log_dir, "job") is True


def test_record_quota_run_does_nothing_when_disabled(log_dir):
    p = QuotaPolicy(max_runs=0)
    record_quota_run(p, log_dir, "job")  # should not raise
    path = get_quota_state_path(log_dir, "job")
    assert not path.exists()


def test_record_quota_run_creates_state_file(log_dir):
    p = QuotaPolicy(max_runs=5)
    record_quota_run(p, log_dir, "job")
    path = get_quota_state_path(log_dir, "job")
    assert path.exists()
    data = json.loads(path.read_text())
    assert len(data["runs"]) == 1
