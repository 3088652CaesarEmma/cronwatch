"""Tests for cronwatch.suppression."""
from datetime import datetime, time
from pathlib import Path

import pytest

from cronwatch.suppression import (
    SuppressionPolicy,
    get_suppression_state_path,
    is_manually_suppressed,
    load_suppression_overrides,
    save_suppression_overrides,
    suppress_until,
)


# ---------------------------------------------------------------------------
# SuppressionPolicy – construction
# ---------------------------------------------------------------------------

def test_suppression_policy_defaults():
    p = SuppressionPolicy()
    assert p.start is None
    assert p.end is None
    assert p.enabled is False


def test_suppression_policy_with_window():
    p = SuppressionPolicy(start=time(22, 0), end=time(6, 0))
    assert p.enabled is True


def test_suppression_policy_mismatched_start_end_raises():
    with pytest.raises(ValueError, match="Both 'start' and 'end'"):
        SuppressionPolicy(start=time(8, 0), end=None)


def test_suppression_policy_mismatched_end_only_raises():
    with pytest.raises(ValueError):
        SuppressionPolicy(start=None, end=time(8, 0))


# ---------------------------------------------------------------------------
# SuppressionPolicy – is_suppressed
# ---------------------------------------------------------------------------

def test_is_suppressed_disabled_policy_returns_false():
    p = SuppressionPolicy()
    assert p.is_suppressed(datetime(2024, 1, 1, 14, 0)) is False


def test_is_suppressed_inside_daytime_window():
    p = SuppressionPolicy(start=time(8, 0), end=time(18, 0))
    assert p.is_suppressed(datetime(2024, 1, 1, 12, 0)) is True


def test_is_suppressed_outside_daytime_window():
    p = SuppressionPolicy(start=time(8, 0), end=time(18, 0))
    assert p.is_suppressed(datetime(2024, 1, 1, 20, 0)) is False


def test_is_suppressed_overnight_window_before_midnight():
    p = SuppressionPolicy(start=time(22, 0), end=time(6, 0))
    assert p.is_suppressed(datetime(2024, 1, 1, 23, 30)) is True


def test_is_suppressed_overnight_window_after_midnight():
    p = SuppressionPolicy(start=time(22, 0), end=time(6, 0))
    assert p.is_suppressed(datetime(2024, 1, 1, 3, 0)) is True


def test_is_suppressed_overnight_window_outside():
    p = SuppressionPolicy(start=time(22, 0), end=time(6, 0))
    assert p.is_suppressed(datetime(2024, 1, 1, 12, 0)) is False


# ---------------------------------------------------------------------------
# SuppressionPolicy – from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    p = SuppressionPolicy.from_config(None)
    assert not p.enabled


def test_from_config_sets_window():
    p = SuppressionPolicy.from_config({"start": "09:00", "end": "17:00"})
    assert p.start == time(9, 0)
    assert p.end == time(17, 0)


def test_from_config_invalid_time_raises():
    with pytest.raises(ValueError):
        SuppressionPolicy.from_config({"start": "25:00", "end": "17:00"})


# ---------------------------------------------------------------------------
# Manual overrides
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_suppression_overrides_empty_when_no_file(log_dir):
    assert load_suppression_overrides(log_dir) == {}


def test_suppress_until_and_is_suppressed(log_dir):
    future = datetime(2099, 12, 31, 23, 59)
    suppress_until(log_dir, "backup", future)
    assert is_manually_suppressed(log_dir, "backup") is True


def test_is_manually_suppressed_expired(log_dir):
    past = datetime(2000, 1, 1, 0, 0)
    suppress_until(log_dir, "backup", past)
    assert is_manually_suppressed(log_dir, "backup") is False


def test_is_manually_suppressed_unknown_job(log_dir):
    assert is_manually_suppressed(log_dir, "unknown_job") is False


def test_get_suppression_state_path_safe_name(log_dir):
    p = get_suppression_state_path(log_dir, "my job/name")
    assert " " not in p.name
    assert "/" not in p.name
