"""Tests for cronwatch.alert throttling module."""

import time
from pathlib import Path

import pytest

from cronwatch.alert import (
    AlertState,
    get_alert_state_path,
    load_alert_states,
    save_alert_states,
    should_alert,
    reset_alert_state,
)


@pytest.fixture
def log_dir(tmp_path):
    return tmp_path


def test_get_alert_state_path_uses_log_dir(log_dir):
    path = get_alert_state_path(log_dir)
    assert path == log_dir / "alert_state.json"


def test_load_alert_states_returns_empty_when_no_file(log_dir):
    states = load_alert_states(log_dir)
    assert states == {}


def test_save_and_load_roundtrip(log_dir):
    states = {
        "backup": AlertState(
            job_name="backup",
            last_alerted_at=1000.0,
            consecutive_failures=3,
            suppressed_count=1,
        )
    }
    save_alert_states(states, log_dir)
    loaded = load_alert_states(log_dir)
    assert "backup" in loaded
    assert loaded["backup"].consecutive_failures == 3
    assert loaded["backup"].suppressed_count == 1


def test_should_alert_first_failure_returns_true(log_dir):
    result = should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    assert result is True


def test_should_alert_success_returns_false(log_dir):
    result = should_alert("myjob", succeeded=True, cooldown_seconds=3600, log_dir=log_dir)
    assert result is False


def test_should_alert_within_cooldown_returns_false(log_dir):
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    result = should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    assert result is False


def test_should_alert_after_cooldown_returns_true(log_dir):
    states = {
        "myjob": AlertState(
            job_name="myjob",
            last_alerted_at=time.time() - 7200,
            consecutive_failures=2,
        )
    }
    save_alert_states(states, log_dir)
    result = should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    assert result is True


def test_should_alert_success_clears_state(log_dir):
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    should_alert("myjob", succeeded=True, cooldown_seconds=3600, log_dir=log_dir)
    states = load_alert_states(log_dir)
    assert "myjob" not in states


def test_suppressed_count_increments(log_dir):
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    states = load_alert_states(log_dir)
    assert states["myjob"].suppressed_count == 2


def test_reset_alert_state_removes_entry(log_dir):
    should_alert("myjob", succeeded=False, cooldown_seconds=3600, log_dir=log_dir)
    reset_alert_state("myjob", log_dir)
    states = load_alert_states(log_dir)
    assert "myjob" not in states


def test_reset_alert_state_nonexistent_is_safe(log_dir):
    reset_alert_state("ghost_job", log_dir)
    states = load_alert_states(log_dir)
    assert "ghost_job" not in states
