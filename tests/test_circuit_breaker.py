"""Tests for cronwatch.circuit_breaker and cronwatch.circuit_breaker_guard."""

from __future__ import annotations

import time
import pytest

from cronwatch.circuit_breaker import (
    CircuitBreakerPolicy,
    get_circuit_state_path,
    load_circuit_state,
    record_failure,
    record_success,
    is_open,
)
from cronwatch.circuit_breaker_guard import CircuitBreakerGuard, CircuitOpenError


# ---------------------------------------------------------------------------
# Policy tests
# ---------------------------------------------------------------------------

def test_circuit_breaker_policy_defaults():
    p = CircuitBreakerPolicy()
    assert p.threshold == 0
    assert p.reset_after == 300
    assert not p.enabled


def test_circuit_breaker_policy_enabled_when_nonzero():
    p = CircuitBreakerPolicy(threshold=3)
    assert p.enabled


def test_circuit_breaker_policy_negative_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        CircuitBreakerPolicy(threshold=-1)


def test_circuit_breaker_policy_zero_reset_after_raises():
    with pytest.raises(ValueError, match="reset_after"):
        CircuitBreakerPolicy(threshold=1, reset_after=0)


def test_from_config_none_returns_defaults():
    p = CircuitBreakerPolicy.from_config(None)
    assert p.threshold == 0


def test_from_config_sets_values():
    p = CircuitBreakerPolicy.from_config({"threshold": 5, "reset_after": 60})
    assert p.threshold == 5
    assert p.reset_after == 60


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def test_get_circuit_state_path_uses_log_dir(tmp_path):
    path = get_circuit_state_path(str(tmp_path), "myjob")
    assert str(tmp_path) in str(path)
    assert "myjob" in path.name


def test_load_circuit_state_returns_defaults_when_no_file(tmp_path):
    state = load_circuit_state(str(tmp_path), "myjob")
    assert state["consecutive_failures"] == 0
    assert state["opened_at"] is None


def test_record_failure_increments_counter(tmp_path):
    policy = CircuitBreakerPolicy(threshold=5)
    state = record_failure(str(tmp_path), "myjob", policy)
    assert state["consecutive_failures"] == 1


def test_record_failure_opens_circuit_at_threshold(tmp_path):
    policy = CircuitBreakerPolicy(threshold=2)
    record_failure(str(tmp_path), "myjob", policy)
    state = record_failure(str(tmp_path), "myjob", policy)
    assert state["opened_at"] is not None


def test_record_success_resets_state(tmp_path):
    policy = CircuitBreakerPolicy(threshold=2)
    record_failure(str(tmp_path), "myjob", policy)
    record_failure(str(tmp_path), "myjob", policy)
    record_success(str(tmp_path), "myjob")
    state = load_circuit_state(str(tmp_path), "myjob")
    assert state["consecutive_failures"] == 0
    assert state["opened_at"] is None


def test_is_open_false_when_disabled(tmp_path):
    policy = CircuitBreakerPolicy(threshold=0)
    assert not is_open(str(tmp_path), "myjob", policy)


def test_is_open_true_when_circuit_open(tmp_path):
    policy = CircuitBreakerPolicy(threshold=1, reset_after=9999)
    record_failure(str(tmp_path), "myjob", policy)
    assert is_open(str(tmp_path), "myjob", policy)


def test_is_open_resets_after_timeout(tmp_path, monkeypatch):
    policy = CircuitBreakerPolicy(threshold=1, reset_after=1)
    record_failure(str(tmp_path), "myjob", policy)
    monkeypatch.setattr(time, "time", lambda: time.time() + 5)
    assert not is_open(str(tmp_path), "myjob", policy)


# ---------------------------------------------------------------------------
# Guard tests
# ---------------------------------------------------------------------------

def test_guard_allows_when_circuit_closed(tmp_path):
    policy = CircuitBreakerPolicy(threshold=3)
    with CircuitBreakerGuard(policy, str(tmp_path), "myjob"):
        pass  # should not raise


def test_guard_raises_when_circuit_open(tmp_path):
    policy = CircuitBreakerPolicy(threshold=1, reset_after=9999)
    record_failure(str(tmp_path), "myjob", policy)
    with pytest.raises(CircuitOpenError):
        with CircuitBreakerGuard(policy, str(tmp_path), "myjob"):
            pass


def test_circuit_open_error_contains_job_name(tmp_path):
    err = CircuitOpenError("important-job")
    assert "important-job" in str(err)


def test_guard_disabled_policy_always_passes(tmp_path):
    policy = CircuitBreakerPolicy(threshold=0)
    record_failure(str(tmp_path), "myjob", policy)
    record_failure(str(tmp_path), "myjob", policy)
    with CircuitBreakerGuard(policy, str(tmp_path), "myjob"):
        pass  # disabled policy must never block
