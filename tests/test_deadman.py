"""Tests for cronwatch.deadman (deadman-switch / silence alerting)."""

import time
from pathlib import Path

import pytest

from cronwatch.deadman import (
    DeadmanPolicy,
    get_deadman_state_path,
    is_overdue,
    load_deadman_states,
    record_job_seen,
    save_deadman_states,
)


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# DeadmanPolicy
# ---------------------------------------------------------------------------

def test_deadman_policy_defaults():
    p = DeadmanPolicy()
    assert p.max_silence_seconds == 0
    assert not p.enabled


def test_deadman_policy_enabled_when_nonzero():
    p = DeadmanPolicy(max_silence_seconds=3600)
    assert p.enabled


def test_deadman_policy_negative_raises():
    with pytest.raises(ValueError):
        DeadmanPolicy(max_silence_seconds=-1)


def test_deadman_policy_from_config():
    p = DeadmanPolicy.from_config({"max_silence_seconds": 7200})
    assert p.max_silence_seconds == 7200


def test_deadman_policy_from_config_empty():
    p = DeadmanPolicy.from_config({})
    assert p.max_silence_seconds == 0


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def test_get_deadman_state_path_uses_log_dir(log_dir):
    path = get_deadman_state_path(log_dir)
    assert path.parent == log_dir
    assert path.name == "deadman_state.json"


def test_load_deadman_states_empty_when_no_file(log_dir):
    states = load_deadman_states(log_dir)
    assert states == {}


def test_save_and_load_roundtrip(log_dir):
    data = {"backup": 1_700_000_000.0, "deploy": 1_700_000_100.0}
    save_deadman_states(data, log_dir)
    loaded = load_deadman_states(log_dir)
    assert loaded == data


def test_record_job_seen_creates_entry(log_dir):
    record_job_seen("nightly", log_dir=log_dir)
    states = load_deadman_states(log_dir)
    assert "nightly" in states
    assert states["nightly"] == pytest.approx(time.time(), abs=5)


def test_record_job_seen_accepts_explicit_timestamp(log_dir):
    ts = 1_000_000.0
    record_job_seen("nightly", log_dir=log_dir, ts=ts)
    assert load_deadman_states(log_dir)["nightly"] == ts


# ---------------------------------------------------------------------------
# is_overdue
# ---------------------------------------------------------------------------

def test_is_overdue_disabled_policy_never_overdue(log_dir):
    policy = DeadmanPolicy(max_silence_seconds=0)
    assert not is_overdue("any_job", policy, log_dir=log_dir)


def test_is_overdue_never_seen_returns_true(log_dir):
    policy = DeadmanPolicy(max_silence_seconds=60)
    assert is_overdue("unknown_job", policy, log_dir=log_dir)


def test_is_overdue_recent_run_returns_false(log_dir):
    policy = DeadmanPolicy(max_silence_seconds=3600)
    record_job_seen("heartbeat", log_dir=log_dir, ts=time.time())
    assert not is_overdue("heartbeat", policy, log_dir=log_dir)


def test_is_overdue_stale_run_returns_true(log_dir):
    policy = DeadmanPolicy(max_silence_seconds=60)
    old_ts = time.time() - 7200  # 2 hours ago
    record_job_seen("stale_job", log_dir=log_dir, ts=old_ts)
    assert is_overdue("stale_job", policy, log_dir=log_dir)
