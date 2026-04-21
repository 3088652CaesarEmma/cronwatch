"""Tests for cronwatch.pin and cronwatch.pin_guard."""
import json
import os
import pytest

from cronwatch.pin import (
    PinPolicy,
    PinViolationError,
    get_pin_state_path,
    load_pin_states,
    save_pin_states,
    record_pin,
    get_pinned_schedule,
)
from cronwatch.pin_guard import PinGuard


# ---------------------------------------------------------------------------
# PinPolicy
# ---------------------------------------------------------------------------

def test_pin_policy_defaults():
    policy = PinPolicy()
    assert policy.schedule is None
    assert not policy.enabled


def test_pin_policy_with_schedule():
    policy = PinPolicy(schedule="0 * * * *")
    assert policy.schedule == "0 * * * *"
    assert policy.enabled


def test_pin_policy_empty_string_becomes_none():
    policy = PinPolicy(schedule="   ")
    assert policy.schedule is None
    assert not policy.enabled


def test_pin_policy_invalid_type_raises():
    with pytest.raises(TypeError):
        PinPolicy(schedule=123)


def test_from_config_none_returns_defaults():
    policy = PinPolicy.from_config(None)
    assert not policy.enabled


def test_from_config_empty_dict_returns_defaults():
    policy = PinPolicy.from_config({})
    assert not policy.enabled


def test_from_config_with_schedule():
    policy = PinPolicy.from_config({"schedule": "*/5 * * * *"})
    assert policy.schedule == "*/5 * * * *"


def test_check_passes_when_disabled():
    policy = PinPolicy()
    policy.check("myjob", "0 * * * *")  # should not raise


def test_check_passes_when_schedule_matches():
    policy = PinPolicy(schedule="0 * * * *")
    policy.check("myjob", "0 * * * *")  # should not raise


def test_check_raises_when_schedule_mismatch():
    policy = PinPolicy(schedule="0 * * * *")
    with pytest.raises(PinViolationError) as exc_info:
        policy.check("myjob", "*/5 * * * *")
    err = exc_info.value
    assert err.job_name == "myjob"
    assert err.expected == "0 * * * *"
    assert err.actual == "*/5 * * * *"
    assert "myjob" in str(err)


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

@pytest.fixture
def log_dir(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    return str(d)


def test_get_pin_state_path_uses_log_dir(log_dir):
    path = get_pin_state_path(log_dir)
    assert path.startswith(log_dir)
    assert path.endswith(".json")


def test_load_pin_states_returns_empty_when_no_file(log_dir):
    assert load_pin_states(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    states = {"job_a": "0 * * * *", "job_b": "*/10 * * * *"}
    save_pin_states(log_dir, states)
    loaded = load_pin_states(log_dir)
    assert loaded == states


def test_record_pin_creates_entry(log_dir):
    record_pin(log_dir, "backup", "0 2 * * *")
    assert get_pinned_schedule(log_dir, "backup") == "0 2 * * *"


def test_get_pinned_schedule_missing_returns_none(log_dir):
    assert get_pinned_schedule(log_dir, "nonexistent") is None


# ---------------------------------------------------------------------------
# PinGuard
# ---------------------------------------------------------------------------

def test_guard_allows_when_policy_disabled():
    policy = PinPolicy()
    with PinGuard(policy, job_name="job", actual_schedule="0 * * * *"):
        pass  # should not raise


def test_guard_allows_when_schedule_matches():
    policy = PinPolicy(schedule="0 * * * *")
    with PinGuard(policy, job_name="job", actual_schedule="0 * * * *"):
        pass  # should not raise


def test_guard_raises_when_schedule_mismatch():
    policy = PinPolicy(schedule="0 * * * *")
    with pytest.raises(PinViolationError):
        with PinGuard(policy, job_name="job", actual_schedule="*/5 * * * *"):
            pass


def test_guard_does_not_suppress_exceptions():
    policy = PinPolicy()
    with pytest.raises(RuntimeError):
        with PinGuard(policy, job_name="job", actual_schedule="0 * * * *"):
            raise RuntimeError("boom")
