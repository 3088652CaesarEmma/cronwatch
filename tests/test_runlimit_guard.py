"""Tests for cronwatch.runlimit_guard."""
from __future__ import annotations

import pytest

from cronwatch.runlimit import RunLimitPolicy, check_run_limit
from cronwatch.runlimit_guard import RunLimitExceededError, RunLimitGuard


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def test_guard_allows_when_under_limit(log_dir):
    policy = RunLimitPolicy(max_runs=3, window_seconds=3600)
    with RunLimitGuard(policy, log_dir, "job"):
        pass  # should not raise


def test_guard_records_run_on_enter(log_dir):
    policy = RunLimitPolicy(max_runs=3, window_seconds=3600)
    with RunLimitGuard(policy, log_dir, "job"):
        pass
    # After one run, 2 more should still be allowed
    assert check_run_limit(policy, log_dir, "job") is True


def test_guard_raises_when_limit_exceeded(log_dir):
    policy = RunLimitPolicy(max_runs=1, window_seconds=3600)
    with RunLimitGuard(policy, log_dir, "job"):
        pass
    with pytest.raises(RunLimitExceededError):
        with RunLimitGuard(policy, log_dir, "job"):
            pass


def test_guard_disabled_policy_always_passes(log_dir):
    policy = RunLimitPolicy(max_runs=0)
    # Entering many times should never raise
    for _ in range(10):
        with RunLimitGuard(policy, log_dir, "job"):
            pass


def test_exceeded_error_message_contains_job_name(log_dir):
    policy = RunLimitPolicy(max_runs=1, window_seconds=600)
    with RunLimitGuard(policy, log_dir, "important_job"):
        pass
    with pytest.raises(RunLimitExceededError) as exc_info:
        with RunLimitGuard(policy, log_dir, "important_job"):
            pass
    assert "important_job" in str(exc_info.value)


def test_exceeded_error_message_contains_max_runs(log_dir):
    policy = RunLimitPolicy(max_runs=2, window_seconds=300)
    with RunLimitGuard(policy, log_dir, "job"):
        pass
    with RunLimitGuard(policy, log_dir, "job"):
        pass
    with pytest.raises(RunLimitExceededError) as exc_info:
        with RunLimitGuard(policy, log_dir, "job"):
            pass
    assert "2" in str(exc_info.value)


def test_exceeded_error_attributes(log_dir):
    policy = RunLimitPolicy(max_runs=1, window_seconds=120)
    with RunLimitGuard(policy, log_dir, "job"):
        pass
    with pytest.raises(RunLimitExceededError) as exc_info:
        with RunLimitGuard(policy, log_dir, "job"):
            pass
    err = exc_info.value
    assert err.job_name == "job"
    assert err.max_runs == 1
    assert err.window_seconds == 120
