"""Tests for cronwatch.streak."""
import json
from pathlib import Path

import pytest

from cronwatch.runner import JobResult
from cronwatch.streak import (
    StreakState,
    get_streak,
    get_streak_path,
    load_streaks,
    record_streak,
    save_streaks,
)


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _result(cmd: str, exit_code: int) -> JobResult:
    return JobResult(command=cmd, exit_code=exit_code, stdout="", stderr="", duration=0.0)


def test_get_streak_path_uses_log_dir(log_dir):
    p = get_streak_path(log_dir)
    assert str(p).startswith(log_dir)
    assert p.name == "streaks.json"


def test_load_streaks_returns_empty_when_no_file(log_dir):
    assert load_streaks(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    state = StreakState(job_name="myjob", current=3, best_success=5, worst_failure=2)
    save_streaks(log_dir, {"myjob": state})
    loaded = load_streaks(log_dir)
    assert "myjob" in loaded
    assert loaded["myjob"].current == 3
    assert loaded["myjob"].best_success == 5
    assert loaded["myjob"].worst_failure == 2


def test_record_streak_success_increments(log_dir):
    r = _result("backup.sh", 0)
    state = record_streak(r, log_dir=log_dir)
    assert state.current == 1


def test_record_streak_consecutive_successes(log_dir):
    r = _result("backup.sh", 0)
    record_streak(r, log_dir=log_dir)
    state = record_streak(r, log_dir=log_dir)
    assert state.current == 2
    assert state.best_success == 2


def test_record_streak_failure_decrements(log_dir):
    r = _result("backup.sh", 1)
    state = record_streak(r, log_dir=log_dir)
    assert state.current == -1
    assert state.worst_failure == 1


def test_record_streak_resets_on_direction_change(log_dir):
    r_ok = _result("job", 0)
    r_fail = _result("job", 1)
    record_streak(r_ok, log_dir=log_dir)
    record_streak(r_ok, log_dir=log_dir)
    state = record_streak(r_fail, log_dir=log_dir)
    # After two successes a failure should reset to -1
    assert state.current == -1
    assert state.best_success == 2


def test_get_streak_returns_none_for_unknown_job(log_dir):
    assert get_streak("unknown", log_dir=log_dir) is None


def test_get_streak_returns_state_after_record(log_dir):
    r = _result("deploy.sh", 0)
    record_streak(r, log_dir=log_dir)
    state = get_streak("deploy.sh", log_dir=log_dir)
    assert state is not None
    assert state.current == 1


def test_streak_state_to_dict_roundtrip():
    s = StreakState(job_name="x", current=-3, best_success=4, worst_failure=3)
    d = s.to_dict()
    s2 = StreakState.from_dict(d)
    assert s2.current == -3
    assert s2.best_success == 4
    assert s2.worst_failure == 3
