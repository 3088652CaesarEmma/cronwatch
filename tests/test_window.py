"""Tests for cronwatch.window."""

from datetime import datetime, time

import pytest

from cronwatch.window import TimeWindow, WindowPolicy, _parse_time


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    assert _parse_time("09:30") == time(9, 30)


def test_parse_time_midnight():
    assert _parse_time("00:00") == time(0, 0)


def test_parse_time_end_of_day():
    assert _parse_time("23:59") == time(23, 59)


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError, match="Invalid time format"):
        _parse_time("9:5")


# ---------------------------------------------------------------------------
# TimeWindow
# ---------------------------------------------------------------------------

def test_time_window_from_str():
    w = TimeWindow.from_str("08:00-17:00")
    assert w.start == time(8, 0)
    assert w.end == time(17, 0)


def test_time_window_start_equals_end_raises():
    with pytest.raises(ValueError, match="before end"):
        TimeWindow(start=time(9, 0), end=time(9, 0))


def test_time_window_start_after_end_raises():
    with pytest.raises(ValueError, match="before end"):
        TimeWindow(start=time(18, 0), end=time(8, 0))


def test_time_window_contains_inside():
    w = TimeWindow(start=time(8, 0), end=time(17, 0))
    assert w.contains(time(12, 0)) is True


def test_time_window_contains_at_start():
    w = TimeWindow(start=time(8, 0), end=time(17, 0))
    assert w.contains(time(8, 0)) is True


def test_time_window_contains_at_end_is_false():
    w = TimeWindow(start=time(8, 0), end=time(17, 0))
    assert w.contains(time(17, 0)) is False


def test_time_window_contains_outside():
    w = TimeWindow(start=time(8, 0), end=time(17, 0))
    assert w.contains(time(20, 0)) is False


# ---------------------------------------------------------------------------
# WindowPolicy
# ---------------------------------------------------------------------------

def test_window_policy_defaults():
    p = WindowPolicy()
    assert p.windows == []
    assert p.enabled is False


def test_window_policy_no_windows_always_allowed():
    p = WindowPolicy()
    assert p.is_allowed(datetime(2024, 1, 1, 3, 0)) is True


def test_window_policy_inside_window_allowed():
    p = WindowPolicy(windows=[TimeWindow.from_str("08:00-17:00")])
    assert p.is_allowed(datetime(2024, 1, 1, 10, 0)) is True


def test_window_policy_outside_window_denied():
    p = WindowPolicy(windows=[TimeWindow.from_str("08:00-17:00")])
    assert p.is_allowed(datetime(2024, 1, 1, 20, 0)) is False


def test_window_policy_multiple_windows():
    p = WindowPolicy(windows=[
        TimeWindow.from_str("06:00-09:00"),
        TimeWindow.from_str("18:00-22:00"),
    ])
    assert p.is_allowed(datetime(2024, 1, 1, 7, 0)) is True
    assert p.is_allowed(datetime(2024, 1, 1, 19, 0)) is True
    assert p.is_allowed(datetime(2024, 1, 1, 12, 0)) is False


def test_window_policy_from_config_none():
    p = WindowPolicy.from_config(None)
    assert p.enabled is False


def test_window_policy_from_config_empty():
    p = WindowPolicy.from_config({})
    assert p.enabled is False


def test_window_policy_from_config_with_windows():
    p = WindowPolicy.from_config({"windows": ["08:00-12:00", "13:00-17:00"]})
    assert len(p.windows) == 2
    assert p.enabled is True


def test_window_policy_from_config_invalid_type_raises():
    with pytest.raises(TypeError):
        WindowPolicy.from_config({"windows": "08:00-17:00"})
