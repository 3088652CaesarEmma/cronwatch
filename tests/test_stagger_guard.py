"""Tests for cronwatch.stagger_guard."""
import pytest
from cronwatch.stagger import StaggerPolicy
from cronwatch.stagger_guard import StaggerGuard


def test_guard_disabled_policy_does_not_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: slept.append(s))
    policy = StaggerPolicy(window_seconds=0)
    with StaggerGuard(policy, job_name="backup"):
        pass
    assert slept == []


def test_guard_enabled_policy_sleeps(monkeypatch):
    slept = []
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: slept.append(s))
    policy = StaggerPolicy(window_seconds=120, seed="test")
    with StaggerGuard(policy, job_name="my_job"):
        pass
    assert len(slept) == 1
    assert 0.0 <= slept[0] <= 120.0


def test_guard_does_not_suppress_exceptions(monkeypatch):
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: None)
    policy = StaggerPolicy(window_seconds=10, seed="s")
    with pytest.raises(RuntimeError, match="boom"):
        with StaggerGuard(policy, job_name="job"):
            raise RuntimeError("boom")


def test_guard_returns_self_on_enter(monkeypatch):
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: None)
    policy = StaggerPolicy(window_seconds=10, seed="s")
    guard = StaggerGuard(policy, job_name="job")
    result = guard.__enter__()
    assert result is guard
    guard.__exit__(None, None, None)


def test_guard_exit_returns_false(monkeypatch):
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: None)
    policy = StaggerPolicy(window_seconds=10, seed="s")
    guard = StaggerGuard(policy, job_name="job")
    guard.__enter__()
    assert guard.__exit__(None, None, None) is False


def test_guard_sleep_amount_matches_policy(monkeypatch):
    slept = []
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: slept.append(s))
    policy = StaggerPolicy(window_seconds=600, seed="consistent")
    expected = policy.delay_for("report_job")
    with StaggerGuard(policy, job_name="report_job"):
        pass
    assert slept == [expected]
