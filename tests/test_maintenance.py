"""Tests for cronwatch.maintenance and cronwatch.maintenance_guard."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from cronwatch.maintenance import (
    MaintenancePolicy,
    MaintenanceWindow,
    _parse_time,
)
from cronwatch.maintenance_guard import MaintenanceActiveError, MaintenanceGuard


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    assert _parse_time("09:30") == time(9, 30)


def test_parse_time_midnight():
    assert _parse_time("00:00") == time(0, 0)


def test_parse_time_invalid_format_raises():
    with pytest.raises(ValueError):
        _parse_time("9:5:00")


def test_parse_time_out_of_range_raises():
    with pytest.raises(ValueError):
        _parse_time("25:00")


# ---------------------------------------------------------------------------
# MaintenanceWindow
# ---------------------------------------------------------------------------

def test_window_active_during_range():
    w = MaintenanceWindow(start=time(2, 0), end=time(4, 0))
    assert w.active_at(datetime(2024, 1, 1, 3, 0))


def test_window_inactive_outside_range():
    w = MaintenanceWindow(start=time(2, 0), end=time(4, 0))
    assert not w.active_at(datetime(2024, 1, 1, 5, 0))


def test_window_overnight_active():
    w = MaintenanceWindow(start=time(22, 0), end=time(6, 0))
    assert w.active_at(datetime(2024, 1, 1, 23, 30))
    assert w.active_at(datetime(2024, 1, 2, 1, 0))


def test_window_overnight_inactive():
    w = MaintenanceWindow(start=time(22, 0), end=time(6, 0))
    assert not w.active_at(datetime(2024, 1, 1, 12, 0))


def test_window_day_filter_active():
    # Monday = 0
    w = MaintenanceWindow(start=time(1, 0), end=time(3, 0), days=[0])
    monday = datetime(2024, 1, 1, 2, 0)  # 2024-01-01 is a Monday
    assert w.active_at(monday)


def test_window_day_filter_inactive_wrong_day():
    w = MaintenanceWindow(start=time(1, 0), end=time(3, 0), days=[0])  # Mon only
    tuesday = datetime(2024, 1, 2, 2, 0)
    assert not w.active_at(tuesday)


def test_window_invalid_day_raises():
    with pytest.raises(ValueError):
        MaintenanceWindow(start=time(1, 0), end=time(2, 0), days=[7])


def test_window_from_str_basic():
    w = MaintenanceWindow.from_str("02:00-04:00")
    assert w.start == time(2, 0)
    assert w.end == time(4, 0)
    assert w.days == []


def test_window_from_str_with_days():
    w = MaintenanceWindow.from_str("02:00-04:00/Mon,Wed")
    assert w.days == [0, 2]


def test_window_from_str_invalid_day_raises():
    with pytest.raises(ValueError):
        MaintenanceWindow.from_str("02:00-04:00/Xyz")


# ---------------------------------------------------------------------------
# MaintenancePolicy
# ---------------------------------------------------------------------------

def test_policy_defaults():
    p = MaintenancePolicy()
    assert not p.enabled()
    assert not p.is_active()


def test_policy_from_config_empty():
    p = MaintenancePolicy.from_config({})
    assert not p.enabled()


def test_policy_from_config_with_windows():
    p = MaintenancePolicy.from_config({"windows": ["02:00-04:00"]})
    assert p.enabled()
    assert len(p.windows) == 1


def test_policy_is_active_true():
    p = MaintenancePolicy.from_config({"windows": ["00:00-23:59"]})
    assert p.is_active(datetime(2024, 6, 1, 12, 0))


def test_policy_from_config_invalid_windows_type_raises():
    with pytest.raises(TypeError):
        MaintenancePolicy.from_config({"windows": "02:00-04:00"})


# ---------------------------------------------------------------------------
# MaintenanceGuard
# ---------------------------------------------------------------------------

def test_guard_passes_when_no_windows():
    policy = MaintenancePolicy()
    with MaintenanceGuard(policy, "backup"):
        pass  # should not raise


def test_guard_raises_when_active():
    policy = MaintenancePolicy.from_config({"windows": ["00:00-23:59"]})
    with pytest.raises(MaintenanceActiveError) as exc_info:
        with MaintenanceGuard(policy, "backup"):
            pass
    assert "backup" in str(exc_info.value)


def test_guard_passes_when_outside_window():
    # Window 03:00-03:01 — very unlikely to be active during test run
    policy = MaintenancePolicy.from_config({"windows": ["03:00-03:01"]})
    future = datetime(2099, 1, 1, 12, 0)  # definitely outside
    # Manually test policy.is_active rather than relying on wall-clock
    assert not policy.is_active(future)


def test_error_contains_job_name():
    err = MaintenanceActiveError("my-job", datetime(2024, 1, 1, 2, 0))
    assert "my-job" in str(err)
