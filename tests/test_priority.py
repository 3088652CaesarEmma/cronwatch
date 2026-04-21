"""Tests for cronwatch.priority and cronwatch.priority_guard."""
import pytest
from dataclasses import dataclass
from cronwatch.priority import (
    PriorityPolicy,
    DEFAULT_PRIORITY,
    sort_jobs_by_priority,
)
from cronwatch.priority_guard import PriorityGuard, PriorityViolationError


# ---------------------------------------------------------------------------
# PriorityPolicy
# ---------------------------------------------------------------------------

def test_priority_policy_defaults():
    p = PriorityPolicy()
    assert p.priority == DEFAULT_PRIORITY


def test_priority_policy_custom_value():
    p = PriorityPolicy(priority=80)
    assert p.priority == 80


def test_priority_policy_boundary_zero():
    p = PriorityPolicy(priority=0)
    assert p.priority == 0


def test_priority_policy_boundary_hundred():
    p = PriorityPolicy(priority=100)
    assert p.priority == 100


def test_priority_policy_above_max_raises():
    with pytest.raises(ValueError, match="between"):
        PriorityPolicy(priority=101)


def test_priority_policy_below_min_raises():
    with pytest.raises(ValueError, match="between"):
        PriorityPolicy(priority=-1)


def test_priority_policy_invalid_type_raises():
    with pytest.raises(TypeError):
        PriorityPolicy(priority="high")  # type: ignore


def test_priority_policy_enabled_when_non_default():
    assert PriorityPolicy(priority=1).enabled is True
    assert PriorityPolicy(priority=99).enabled is True


def test_priority_policy_not_enabled_at_default():
    assert PriorityPolicy().enabled is False


def test_is_higher_than():
    high = PriorityPolicy(priority=80)
    low = PriorityPolicy(priority=20)
    assert high.is_higher_than(low) is True
    assert low.is_higher_than(high) is False


def test_is_lower_than():
    high = PriorityPolicy(priority=80)
    low = PriorityPolicy(priority=20)
    assert low.is_lower_than(high) is True
    assert high.is_lower_than(low) is False


def test_from_config_none_returns_defaults():
    p = PriorityPolicy.from_config(None)
    assert p.priority == DEFAULT_PRIORITY


def test_from_config_empty_dict_returns_defaults():
    p = PriorityPolicy.from_config({})
    assert p.priority == DEFAULT_PRIORITY


def test_from_config_sets_priority():
    p = PriorityPolicy.from_config({"priority": 75})
    assert p.priority == 75


# ---------------------------------------------------------------------------
# sort_jobs_by_priority
# ---------------------------------------------------------------------------

@dataclass
class _FakeJob:
    name: str
    priority: PriorityPolicy


def test_sort_jobs_highest_first():
    jobs = [
        _FakeJob("a", PriorityPolicy(priority=10)),
        _FakeJob("b", PriorityPolicy(priority=90)),
        _FakeJob("c", PriorityPolicy(priority=50)),
    ]
    result = sort_jobs_by_priority(jobs)
    assert [j.name for j in result] == ["b", "c", "a"]


def test_sort_jobs_lowest_first():
    jobs = [
        _FakeJob("a", PriorityPolicy(priority=10)),
        _FakeJob("b", PriorityPolicy(priority=90)),
    ]
    result = sort_jobs_by_priority(jobs, reverse=True)
    assert result[0].name == "a"


# ---------------------------------------------------------------------------
# PriorityGuard
# ---------------------------------------------------------------------------

def test_guard_allows_when_above_minimum():
    policy = PriorityPolicy(priority=60)
    with PriorityGuard("myjob", policy, min_priority=50):
        pass  # should not raise


def test_guard_allows_when_equal_to_minimum():
    policy = PriorityPolicy(priority=50)
    with PriorityGuard("myjob", policy, min_priority=50):
        pass


def test_guard_raises_when_below_minimum():
    policy = PriorityPolicy(priority=20)
    with pytest.raises(PriorityViolationError):
        with PriorityGuard("myjob", policy, min_priority=50):
            pass


def test_violation_error_contains_job_name():
    policy = PriorityPolicy(priority=10)
    with pytest.raises(PriorityViolationError) as exc_info:
        with PriorityGuard("critical_job", policy, min_priority=50):
            pass
    assert "critical_job" in str(exc_info.value)


def test_violation_error_contains_priority_values():
    policy = PriorityPolicy(priority=10)
    with pytest.raises(PriorityViolationError) as exc_info:
        with PriorityGuard("myjob", policy, min_priority=50):
            pass
    assert "10" in str(exc_info.value)
    assert "50" in str(exc_info.value)


def test_guard_default_min_priority_always_passes():
    policy = PriorityPolicy(priority=0)
    with PriorityGuard("myjob", policy):
        pass
