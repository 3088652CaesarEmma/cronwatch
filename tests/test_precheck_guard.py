"""Tests for cronwatch.precheck_guard."""
import pytest
from cronwatch.precheck import PrecheckPolicy, PrecheckFailedError
from cronwatch.precheck_guard import PrecheckGuard


def test_guard_allows_when_policy_disabled():
    policy = PrecheckPolicy()
    with PrecheckGuard(policy, "myjob"):
        pass  # should not raise


def test_guard_allows_when_all_checks_pass():
    policy = PrecheckPolicy(checks=["true"])
    with PrecheckGuard(policy, "myjob"):
        pass  # should not raise


def test_guard_raises_when_check_fails():
    policy = PrecheckPolicy(checks=["false"])
    with pytest.raises(PrecheckFailedError):
        with PrecheckGuard(policy, "myjob"):
            pass


def test_guard_returns_self_on_enter():
    policy = PrecheckPolicy()
    guard = PrecheckGuard(policy, "myjob")
    result = guard.__enter__()
    assert result is guard
    guard.__exit__(None, None, None)


def test_guard_does_not_suppress_exceptions():
    policy = PrecheckPolicy()
    with pytest.raises(RuntimeError):
        with PrecheckGuard(policy, "myjob"):
            raise RuntimeError("boom")


def test_guard_exit_returns_false():
    policy = PrecheckPolicy()
    guard = PrecheckGuard(policy, "myjob")
    guard.__enter__()
    assert guard.__exit__(None, None, None) is False
