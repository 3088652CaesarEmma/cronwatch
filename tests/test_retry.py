"""Tests for cronwatch.retry."""

from __future__ import annotations

import pytest

from cronwatch.retry import RetryPolicy, RetryResult, run_with_retry, policy_from_config
from cronwatch.runner import JobResult


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

def test_retry_policy_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 1
    assert p.delay_seconds == 5.0
    assert p.backoff_factor == 1.0


def test_retry_policy_invalid_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)


def test_retry_policy_invalid_delay():
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryPolicy(delay_seconds=-1)


def test_retry_policy_invalid_backoff():
    with pytest.raises(ValueError, match="backoff_factor"):
        RetryPolicy(backoff_factor=0.5)


def test_delay_for_first_attempt_is_zero():
    p = RetryPolicy(delay_seconds=10.0)
    assert p.delay_for(0) == 0.0


def test_delay_for_second_attempt():
    p = RetryPolicy(delay_seconds=10.0, backoff_factor=2.0)
    assert p.delay_for(1) == 10.0
    assert p.delay_for(2) == 20.0


# ---------------------------------------------------------------------------
# run_with_retry
# ---------------------------------------------------------------------------

def _no_sleep(seconds: float) -> None:  # noqa: ARG001
    pass


def test_success_on_first_attempt():
    result = run_with_retry("true", RetryPolicy(max_attempts=3), sleep_fn=_no_sleep)
    assert result.attempts == 1
    assert result.succeeded is True


def test_failure_exhausts_attempts():
    result = run_with_retry("false", RetryPolicy(max_attempts=3), sleep_fn=_no_sleep)
    assert result.attempts == 3
    assert result.succeeded is False


def test_sleep_called_between_retries():
    delays: list[float] = []
    run_with_retry(
        "false",
        RetryPolicy(max_attempts=3, delay_seconds=2.0),
        sleep_fn=delays.append,
    )
    # First attempt has no sleep; 2nd and 3rd do
    assert len(delays) == 2
    assert all(d == 2.0 for d in delays)


def test_final_result_is_last():
    result = run_with_retry("false", RetryPolicy(max_attempts=2), sleep_fn=_no_sleep)
    assert result.final is result.results[-1]


# ---------------------------------------------------------------------------
# policy_from_config
# ---------------------------------------------------------------------------

def test_policy_from_config_full():
    cfg = {"retry_attempts": "4", "retry_delay": "3.5", "retry_backoff": "2.0"}
    p = policy_from_config(cfg)
    assert p.max_attempts == 4
    assert p.delay_seconds == 3.5
    assert p.backoff_factor == 2.0


def test_policy_from_config_defaults():
    p = policy_from_config({})
    assert p.max_attempts == 1
    assert p.delay_seconds == 5.0
    assert p.backoff_factor == 1.0
