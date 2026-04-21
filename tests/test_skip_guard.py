"""Tests for cronwatch.skip_guard (SkipGuard context manager)."""
import pytest

from cronwatch.skip import JobSkippedError, SkipPolicy
from cronwatch.skip_guard import SkipGuard


def test_guard_allows_when_policy_disabled():
    policy = SkipPolicy()  # no skip_if
    with SkipGuard(policy, job_name="myjob"):
        pass  # should not raise


def test_guard_allows_when_condition_not_met():
    policy = SkipPolicy(skip_if="false")  # exits 1 → do not skip
    with SkipGuard(policy, job_name="myjob"):
        pass  # should not raise


def test_guard_raises_when_condition_met():
    policy = SkipPolicy(skip_if="true")  # exits 0 → skip
    with pytest.raises(JobSkippedError) as exc_info:
        with SkipGuard(policy, job_name="backup"):
            pass
    assert exc_info.value.job_name == "backup"


def test_guard_error_contains_skip_if_command():
    policy = SkipPolicy(skip_if="true")
    with pytest.raises(JobSkippedError) as exc_info:
        with SkipGuard(policy, job_name="sync"):
            pass
    assert "true" in str(exc_info.value)


def test_guard_exit_does_not_suppress_exceptions():
    policy = SkipPolicy()  # disabled
    guard = SkipGuard(policy, job_name="myjob")
    guard.__enter__()
    result = guard.__exit__(ValueError, ValueError("boom"), None)
    assert result is False


def test_guard_disabled_policy_never_raises():
    policy = SkipPolicy.from_config(None)
    for _ in range(3):
        with SkipGuard(policy, job_name="job"):
            pass
