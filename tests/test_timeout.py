"""Tests for cronwatch.timeout module."""

import platform
import time

import pytest

from cronwatch.timeout import (
    JobTimeoutError,
    TimeoutPolicy,
    enforce_timeout,
)


# ---------------------------------------------------------------------------
# TimeoutPolicy
# ---------------------------------------------------------------------------

def test_timeout_policy_defaults():
    policy = TimeoutPolicy()
    assert policy.seconds is None
    assert policy.kill_on_timeout is True
    assert policy.enabled is False


def test_timeout_policy_with_seconds():
    policy = TimeoutPolicy(seconds=30)
    assert policy.seconds == 30
    assert policy.enabled is True


def test_timeout_policy_invalid_seconds():
    with pytest.raises(ValueError, match="positive integer"):
        TimeoutPolicy(seconds=0)


def test_timeout_policy_negative_seconds():
    with pytest.raises(ValueError, match="positive integer"):
        TimeoutPolicy(seconds=-5)


def test_timeout_policy_from_config():
    cfg = {"timeout": 60, "kill_on_timeout": False}
    policy = TimeoutPolicy.from_config(cfg)
    assert policy.seconds == 60
    assert policy.kill_on_timeout is False


def test_timeout_policy_from_config_missing_keys():
    policy = TimeoutPolicy.from_config({})
    assert policy.seconds is None
    assert policy.kill_on_timeout is True


# ---------------------------------------------------------------------------
# JobTimeoutError
# ---------------------------------------------------------------------------

def test_job_timeout_error_message():
    err = JobTimeoutError(10)
    assert "10" in str(err)
    assert err.seconds == 10


# ---------------------------------------------------------------------------
# enforce_timeout context manager
# ---------------------------------------------------------------------------

@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM not available")
def test_enforce_timeout_raises_on_slow_block():
    policy = TimeoutPolicy(seconds=1)
    with pytest.raises(JobTimeoutError) as exc_info:
        with enforce_timeout(policy):
            time.sleep(5)
    assert exc_info.value.seconds == 1


@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM not available")
def test_enforce_timeout_does_not_raise_when_fast():
    policy = TimeoutPolicy(seconds=5)
    with enforce_timeout(policy):
        pass  # completes instantly


def test_enforce_timeout_disabled_policy_does_nothing():
    policy = TimeoutPolicy()  # no seconds
    with enforce_timeout(policy):
        pass  # should never raise


@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM not available")
def test_enforce_timeout_restores_alarm_after_block():
    import signal
    policy = TimeoutPolicy(seconds=10)
    with enforce_timeout(policy):
        pass
    # alarm should be cancelled (0 means no pending alarm)
    remaining = signal.alarm(0)
    assert remaining == 0
