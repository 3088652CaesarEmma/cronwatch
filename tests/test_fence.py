"""Tests for cronwatch.fence (FencePolicy + FenceGuard)."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.fence import FencePolicy, FenceGuard, FenceViolationError


# ---------------------------------------------------------------------------
# FencePolicy — construction
# ---------------------------------------------------------------------------

def test_fence_policy_defaults():
    p = FencePolicy()
    assert p.not_before is None
    assert p.not_after is None
    assert p.enabled is False


def test_fence_policy_with_not_before():
    d = datetime.date(2025, 1, 1)
    p = FencePolicy(not_before=d)
    assert p.not_before == d
    assert p.enabled is True


def test_fence_policy_with_not_after():
    d = datetime.date(2099, 12, 31)
    p = FencePolicy(not_after=d)
    assert p.not_after == d
    assert p.enabled is True


def test_fence_policy_not_before_after_not_after_raises():
    with pytest.raises(ValueError, match="not_before must not be later"):
        FencePolicy(
            not_before=datetime.date(2030, 6, 1),
            not_after=datetime.date(2025, 1, 1),
        )


def test_fence_policy_invalid_not_before_type_raises():
    with pytest.raises(TypeError):
        FencePolicy(not_before="2025-01-01")  # type: ignore[arg-type]


def test_fence_policy_invalid_not_after_type_raises():
    with pytest.raises(TypeError):
        FencePolicy(not_after=20991231)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FencePolicy.check
# ---------------------------------------------------------------------------

def test_check_disabled_policy_never_raises():
    p = FencePolicy()
    p.check("myjob", today=datetime.date(1900, 1, 1))  # no error


def test_check_before_not_before_raises():
    p = FencePolicy(not_before=datetime.date(2030, 1, 1))
    with pytest.raises(FenceViolationError, match="before activation date"):
        p.check("myjob", today=datetime.date(2025, 6, 15))


def test_check_after_not_after_raises():
    p = FencePolicy(not_after=datetime.date(2020, 12, 31))
    with pytest.raises(FenceViolationError, match="after expiry date"):
        p.check("myjob", today=datetime.date(2025, 1, 1))


def test_check_within_range_does_not_raise():
    p = FencePolicy(
        not_before=datetime.date(2025, 1, 1),
        not_after=datetime.date(2099, 12, 31),
    )
    p.check("myjob", today=datetime.date(2025, 6, 15))  # no error


def test_violation_error_contains_job_name():
    p = FencePolicy(not_before=datetime.date(2099, 1, 1))
    with pytest.raises(FenceViolationError) as exc_info:
        p.check("important-job", today=datetime.date(2025, 1, 1))
    assert "important-job" in str(exc_info.value)


# ---------------------------------------------------------------------------
# FencePolicy.from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    p = FencePolicy.from_config(None)
    assert p.enabled is False


def test_from_config_empty_dict_returns_defaults():
    p = FencePolicy.from_config({})
    assert p.enabled is False


def test_from_config_string_dates_parsed():
    p = FencePolicy.from_config({"not_before": "2025-03-01", "not_after": "2099-03-01"})
    assert p.not_before == datetime.date(2025, 3, 1)
    assert p.not_after == datetime.date(2099, 3, 1)


def test_from_config_date_objects_accepted():
    d = datetime.date(2025, 6, 1)
    p = FencePolicy.from_config({"not_before": d})
    assert p.not_before == d


# ---------------------------------------------------------------------------
# FenceGuard
# ---------------------------------------------------------------------------

def test_guard_allows_when_within_fence(monkeypatch):
    today = datetime.date(2025, 6, 15)
    p = FencePolicy(
        not_before=datetime.date(2025, 1, 1),
        not_after=datetime.date(2099, 12, 31),
    )
    monkeypatch.setattr(datetime, "date", type("_D", (), {"today": staticmethod(lambda: today), **{k: getattr(datetime.date, k) for k in dir(datetime.date) if not k.startswith("__")}}))
    with FenceGuard(p, "myjob"):
        pass  # should not raise


def test_guard_raises_when_outside_fence():
    p = FencePolicy(not_after=datetime.date(2000, 1, 1))
    with pytest.raises(FenceViolationError):
        with FenceGuard(p, "old-job"):
            pass


def test_guard_disabled_policy_always_passes():
    p = FencePolicy()
    with FenceGuard(p, "anyjob"):
        pass  # no error


def test_guard_does_not_suppress_exceptions():
    p = FencePolicy()
    with pytest.raises(RuntimeError, match="boom"):
        with FenceGuard(p, "anyjob"):
            raise RuntimeError("boom")
