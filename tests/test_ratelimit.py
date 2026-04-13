"""Tests for cronwatch.ratelimit."""

import time
from pathlib import Path

import pytest

from cronwatch.ratelimit import (
    RateLimitPolicy,
    get_ratelimit_state_path,
    is_rate_limited,
    load_ratelimit_state,
    record_notification,
    save_ratelimit_state,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    return d


# --- RateLimitPolicy ---

def test_ratelimit_policy_defaults():
    p = RateLimitPolicy()
    assert p.min_interval_seconds == 3600
    assert p.enabled is True


def test_ratelimit_policy_zero_disables():
    p = RateLimitPolicy(min_interval_seconds=0)
    assert p.enabled is False


def test_ratelimit_policy_negative_raises():
    with pytest.raises(ValueError):
        RateLimitPolicy(min_interval_seconds=-1)


def test_ratelimit_policy_from_config():
    p = RateLimitPolicy.from_config({"min_interval_seconds": 300})
    assert p.min_interval_seconds == 300


def test_ratelimit_policy_from_config_defaults():
    p = RateLimitPolicy.from_config({})
    assert p.min_interval_seconds == 3600


# --- State path ---

def test_get_ratelimit_state_path_uses_log_dir(log_dir):
    path = get_ratelimit_state_path(log_dir)
    assert path.parent == log_dir
    assert path.name == "ratelimit_state.json"


# --- Load / save roundtrip ---

def test_load_returns_empty_when_no_file(log_dir):
    assert load_ratelimit_state(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    state = {"job_a": 1700000000.0, "job_b": 1700001000.0}
    save_ratelimit_state(state, log_dir)
    loaded = load_ratelimit_state(log_dir)
    assert loaded == state


# --- is_rate_limited ---

def test_not_rate_limited_when_no_previous_record(log_dir):
    policy = RateLimitPolicy(min_interval_seconds=60)
    assert is_rate_limited("my_job", policy, log_dir) is False


def test_rate_limited_within_interval(log_dir):
    policy = RateLimitPolicy(min_interval_seconds=3600)
    now = time.time()
    save_ratelimit_state({"my_job": now - 100}, log_dir)
    assert is_rate_limited("my_job", policy, log_dir, _now=now) is True


def test_not_rate_limited_after_interval(log_dir):
    policy = RateLimitPolicy(min_interval_seconds=3600)
    now = time.time()
    save_ratelimit_state({"my_job": now - 7200}, log_dir)
    assert is_rate_limited("my_job", policy, log_dir, _now=now) is False


def test_disabled_policy_never_rate_limits(log_dir):
    policy = RateLimitPolicy(min_interval_seconds=0)
    now = time.time()
    save_ratelimit_state({"my_job": now}, log_dir)  # just notified
    assert is_rate_limited("my_job", policy, log_dir, _now=now) is False


# --- record_notification ---

def test_record_notification_persists_timestamp(log_dir):
    fake_now = 1700005000.0
    record_notification("job_x", log_dir, _now=fake_now)
    state = load_ratelimit_state(log_dir)
    assert state["job_x"] == fake_now


def test_record_notification_updates_existing(log_dir):
    record_notification("job_x", log_dir, _now=1000.0)
    record_notification("job_x", log_dir, _now=2000.0)
    state = load_ratelimit_state(log_dir)
    assert state["job_x"] == 2000.0
