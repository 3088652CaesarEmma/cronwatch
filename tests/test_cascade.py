"""Tests for cronwatch.cascade and cronwatch.cascade_guard."""
import pytest

from cronwatch.cascade import CascadePolicy
from cronwatch.cascade_guard import CascadeGuard
from cronwatch.runner import JobResult


# ---------------------------------------------------------------------------
# CascadePolicy tests
# ---------------------------------------------------------------------------

def test_cascade_policy_defaults():
    p = CascadePolicy()
    assert p.on_success == []
    assert p.on_failure == []
    assert p.enabled is False


def test_cascade_policy_with_jobs():
    p = CascadePolicy(on_success=["job_a"], on_failure=["job_b"])
    assert p.on_success == ["job_a"]
    assert p.on_failure == ["job_b"]
    assert p.enabled is True


def test_cascade_policy_strips_whitespace():
    p = CascadePolicy(on_success=[" job_a "], on_failure=[" job_b "])
    assert p.on_success == ["job_a"]
    assert p.on_failure == ["job_b"]


def test_cascade_policy_invalid_on_success_type_raises():
    with pytest.raises(TypeError):
        CascadePolicy(on_success="not-a-list")


def test_cascade_policy_invalid_on_failure_type_raises():
    with pytest.raises(TypeError):
        CascadePolicy(on_failure="not-a-list")


def test_cascade_policy_empty_string_in_on_success_raises():
    with pytest.raises(ValueError):
        CascadePolicy(on_success=[""])


def test_cascade_policy_empty_string_in_on_failure_raises():
    with pytest.raises(ValueError):
        CascadePolicy(on_failure=[""])


def test_cascade_policy_enabled_only_on_success():
    p = CascadePolicy(on_success=["next_job"])
    assert p.enabled is True


def test_cascade_policy_jobs_for_success():
    p = CascadePolicy(on_success=["a", "b"], on_failure=["c"])
    assert p.jobs_for(True) == ["a", "b"]


def test_cascade_policy_jobs_for_failure():
    p = CascadePolicy(on_success=["a"], on_failure=["c", "d"])
    assert p.jobs_for(False) == ["c", "d"]


def test_from_config_none_returns_defaults():
    p = CascadePolicy.from_config(None)
    assert p.on_success == []
    assert p.on_failure == []


def test_from_config_empty_dict_returns_defaults():
    p = CascadePolicy.from_config({})
    assert p.on_success == []
    assert p.on_failure == []


def test_from_config_populates_fields():
    p = CascadePolicy.from_config({"on_success": ["job_x"], "on_failure": ["job_y"]})
    assert p.on_success == ["job_x"]
    assert p.on_failure == ["job_y"]


# ---------------------------------------------------------------------------
# CascadeGuard tests
# ---------------------------------------------------------------------------

def _make_result(exit_code: int) -> JobResult:
    return JobResult(
        command="echo hi",
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=0.1,
    )


def test_guard_triggers_on_success():
    triggered = []
    policy = CascadePolicy(on_success=["next"])
    guard = CascadeGuard(policy, triggered.extend)
    with guard:
        guard.set_result(_make_result(0))
    assert triggered == ["next"]


def test_guard_triggers_on_failure():
    triggered = []
    policy = CascadePolicy(on_failure=["fallback"])
    guard = CascadeGuard(policy, triggered.extend)
    with guard:
        guard.set_result(_make_result(1))
    assert triggered == ["fallback"]


def test_guard_disabled_policy_does_not_trigger():
    triggered = []
    policy = CascadePolicy()
    guard = CascadeGuard(policy, triggered.extend)
    with guard:
        guard.set_result(_make_result(0))
    assert triggered == []


def test_guard_no_result_does_not_trigger():
    triggered = []
    policy = CascadePolicy(on_success=["next"])
    guard = CascadeGuard(policy, triggered.extend)
    with guard:
        pass
    assert triggered == []


def test_guard_does_not_suppress_exceptions():
    policy = CascadePolicy(on_success=["next"])
    guard = CascadeGuard(policy, lambda jobs: None)
    with pytest.raises(RuntimeError):
        with guard:
            raise RuntimeError("boom")
