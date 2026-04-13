"""Tests for cronwatch.throttle."""
import json
import time
from pathlib import Path

import pytest

from cronwatch.throttle import (
    ThrottlePolicy,
    get_throttle_state_path,
    load_throttle_state,
    record_notification,
    save_throttle_state,
    should_throttle,
)


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- ThrottlePolicy ---

def test_throttle_policy_defaults():
    policy = ThrottlePolicy()
    assert policy.min_interval == 0
    assert not policy.enabled


def test_throttle_policy_with_interval():
    policy = ThrottlePolicy(min_interval=300)
    assert policy.min_interval == 300
    assert policy.enabled


def test_throttle_policy_negative_raises():
    with pytest.raises(ValueError):
        ThrottlePolicy(min_interval=-1)


def test_throttle_policy_zero_disables():
    policy = ThrottlePolicy(min_interval=0)
    assert not policy.enabled


def test_throttle_policy_from_config_none_returns_defaults():
    policy = ThrottlePolicy.from_config(None)
    assert policy.min_interval == 0


def test_throttle_policy_from_config_sets_interval():
    policy = ThrottlePolicy.from_config({"min_interval": 600})
    assert policy.min_interval == 600


# --- State helpers ---

def test_get_throttle_state_path_uses_log_dir(log_dir):
    path = get_throttle_state_path(log_dir)
    assert path.parent == log_dir
    assert path.name == "throttle_state.json"


def test_load_throttle_state_returns_empty_when_no_file(log_dir):
    state = load_throttle_state(log_dir)
    assert state == {}


def test_save_and_load_roundtrip(log_dir):
    data = {"my_job": 1234567890.0}
    save_throttle_state(data, log_dir)
    loaded = load_throttle_state(log_dir)
    assert loaded == data


def test_load_throttle_state_handles_corrupt_file(log_dir):
    path = get_throttle_state_path(log_dir)
    path.write_text("not valid json")
    state = load_throttle_state(log_dir)
    assert state == {}


# --- should_throttle / record_notification ---

def test_should_throttle_disabled_policy_returns_false(log_dir):
    policy = ThrottlePolicy(min_interval=0)
    assert not should_throttle("job", policy, log_dir)


def test_should_throttle_no_prior_record_returns_false(log_dir):
    policy = ThrottlePolicy(min_interval=300)
    assert not should_throttle("job", policy, log_dir)


def test_should_throttle_recent_notification_returns_true(log_dir):
    policy = ThrottlePolicy(min_interval=300)
    record_notification("job", log_dir)
    assert should_throttle("job", policy, log_dir)


def test_should_throttle_old_notification_returns_false(log_dir):
    policy = ThrottlePolicy(min_interval=1)
    state = {"job": time.time() - 10}
    save_throttle_state(state, log_dir)
    assert not should_throttle("job", policy, log_dir)


def test_record_notification_creates_state_file(log_dir):
    record_notification("my_job", log_dir)
    path = get_throttle_state_path(log_dir)
    assert path.exists()
    data = json.loads(path.read_text())
    assert "my_job" in data
