"""Tests for cronwatch.window_guard."""

from datetime import datetime

import pytest

from cronwatch.window import TimeWindow, WindowPolicy
from cronwatch.window_guard import WindowGuard, WindowViolationError


_OPEN_POLICY = WindowPolicy(windows=[TimeWindow.from_str("08:00-18:00")])
_CLOSED_POLICY = WindowPolicy(windows=[TimeWindow.from_str("08:00-09:00")])
_DISABLED_POLICY = WindowPolicy()  # no windows — always open

_INSIDE = datetime(2024, 6, 1, 10, 0)   # 10:00 — inside 08:00-18:00
_OUTSIDE = datetime(2024, 6, 1, 20, 0)  # 20:00 — outside 08:00-18:00
_EARLY = datetime(2024, 6, 1, 8, 30)    # 08:30 — inside 08:00-09:00
_LATE = datetime(2024, 6, 1, 9, 30)     # 09:30 — outside 08:00-09:00


def test_guard_allows_when_inside_window():
    with WindowGuard(_OPEN_POLICY, job_name="test", now=_INSIDE):
        pass  # should not raise


def test_guard_raises_when_outside_window():
    with pytest.raises(WindowViolationError):
        with WindowGuard(_OPEN_POLICY, job_name="test", now=_OUTSIDE):
            pass


def test_guard_disabled_policy_always_passes():
    with WindowGuard(_DISABLED_POLICY, job_name="test", now=_OUTSIDE):
        pass  # no windows configured — always allowed


def test_violation_error_contains_job_name():
    with pytest.raises(WindowViolationError) as exc_info:
        with WindowGuard(_OPEN_POLICY, job_name="my-job", now=_OUTSIDE):
            pass
    assert "my-job" in str(exc_info.value)


def test_violation_error_contains_time():
    with pytest.raises(WindowViolationError) as exc_info:
        with WindowGuard(_OPEN_POLICY, job_name="job", now=_OUTSIDE):
            pass
    assert "20:00" in str(exc_info.value)


def test_violation_error_attributes():
    err = WindowViolationError("backup", _OUTSIDE)
    assert err.job_name == "backup"
    assert err.dt == _OUTSIDE


def test_guard_does_not_suppress_inner_exception():
    with pytest.raises(RuntimeError, match="inner"):
        with WindowGuard(_OPEN_POLICY, job_name="job", now=_INSIDE):
            raise RuntimeError("inner")


def test_guard_narrow_window_inside():
    with WindowGuard(_CLOSED_POLICY, job_name="job", now=_EARLY):
        pass


def test_guard_narrow_window_outside():
    with pytest.raises(WindowViolationError):
        with WindowGuard(_CLOSED_POLICY, job_name="job", now=_LATE):
            pass
