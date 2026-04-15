"""Tests for cronwatch.pause."""

import pytest

from cronwatch.pause import (
    get_pause_state_path,
    is_paused,
    list_paused,
    load_pause_state,
    pause_job,
    resume_job,
    save_pause_state,
)


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def test_get_pause_state_path_uses_log_dir(log_dir):
    path = get_pause_state_path(log_dir)
    assert str(path).startswith(log_dir)
    assert path.name == "paused_jobs.json"


def test_load_pause_state_returns_empty_when_no_file(log_dir):
    state = load_pause_state(log_dir)
    assert state == {}


def test_save_and_load_roundtrip(log_dir):
    state = {"backup": True, "cleanup": True}
    save_pause_state(state, log_dir)
    loaded = load_pause_state(log_dir)
    assert loaded == state


def test_pause_job_marks_job(log_dir):
    pause_job("myjob", log_dir)
    assert is_paused("myjob", log_dir) is True


def test_resume_job_clears_flag(log_dir):
    pause_job("myjob", log_dir)
    resume_job("myjob", log_dir)
    assert is_paused("myjob", log_dir) is False


def test_is_paused_returns_false_for_unknown_job(log_dir):
    assert is_paused("nonexistent", log_dir) is False


def test_resume_nonexistent_job_is_noop(log_dir):
    resume_job("ghost", log_dir)  # should not raise
    assert is_paused("ghost", log_dir) is False


def test_list_paused_returns_sorted_names(log_dir):
    for name in ["zebra", "alpha", "mango"]:
        pause_job(name, log_dir)
    assert list_paused(log_dir) == ["alpha", "mango", "zebra"]


def test_list_paused_excludes_resumed_jobs(log_dir):
    pause_job("job_a", log_dir)
    pause_job("job_b", log_dir)
    resume_job("job_a", log_dir)
    assert list_paused(log_dir) == ["job_b"]


def test_list_paused_empty_when_no_paused_jobs(log_dir):
    assert list_paused(log_dir) == []
