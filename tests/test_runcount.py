"""Tests for cronwatch.runcount and cronwatch.runcount_guard."""
from __future__ import annotations

import json
import pytest

from cronwatch.runcount import (
    get_runcount_path,
    load_runcounts,
    save_runcounts,
    increment,
    get_count,
    reset,
    record_result,
)
from cronwatch.runcount_guard import RunCountGuard, RunCountExceededError
from cronwatch.runner import JobResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def sample_result():
    return JobResult(
        command="echo hello",
        exit_code=0,
        stdout="hello\n",
        stderr="",
        duration=0.1,
    )


# ---------------------------------------------------------------------------
# runcount module
# ---------------------------------------------------------------------------

def test_get_runcount_path_uses_log_dir(log_dir):
    path = get_runcount_path(log_dir)
    assert str(path).startswith(log_dir)
    assert path.name == "runcount.json"


def test_load_runcounts_returns_empty_when_no_file(log_dir):
    assert load_runcounts(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    data = {"job_a": 3, "job_b": 7}
    save_runcounts(data, log_dir)
    assert load_runcounts(log_dir) == data


def test_increment_creates_entry(log_dir):
    count = increment("my_job", log_dir)
    assert count == 1


def test_increment_accumulates(log_dir):
    for i in range(1, 6):
        count = increment("my_job", log_dir)
        assert count == i


def test_get_count_returns_zero_for_unknown_job(log_dir):
    assert get_count("unknown", log_dir) == 0


def test_get_count_reflects_increments(log_dir):
    increment("job_x", log_dir)
    increment("job_x", log_dir)
    assert get_count("job_x", log_dir) == 2


def test_reset_sets_count_to_zero(log_dir):
    increment("job_y", log_dir)
    increment("job_y", log_dir)
    reset("job_y", log_dir)
    assert get_count("job_y", log_dir) == 0


def test_record_result_increments_by_command(log_dir, sample_result):
    count = record_result(sample_result, log_dir)
    assert count == 1
    assert get_count(sample_result.command, log_dir) == 1


# ---------------------------------------------------------------------------
# RunCountGuard
# ---------------------------------------------------------------------------

def test_guard_disabled_when_max_runs_is_zero(log_dir):
    """max_runs=0 should never raise regardless of current count."""
    for _ in range(10):
        increment("job_z", log_dir)
    with RunCountGuard("job_z", max_runs=0, log_dir=log_dir):
        pass  # should not raise


def test_guard_disabled_when_max_runs_is_none(log_dir):
    with RunCountGuard("job_z", max_runs=None, log_dir=log_dir):
        pass


def test_guard_allows_under_limit(log_dir):
    with RunCountGuard("limited_job", max_runs=5, log_dir=log_dir):
        pass
    assert get_count("limited_job", log_dir) == 1


def test_guard_increments_on_enter(log_dir):
    for _ in range(3):
        with RunCountGuard("counter_job", max_runs=10, log_dir=log_dir):
            pass
    assert get_count("counter_job", log_dir) == 3


def test_guard_raises_when_limit_exceeded(log_dir):
    for _ in range(2):
        increment("capped_job", log_dir)
    with pytest.raises(RunCountExceededError) as exc_info:
        with RunCountGuard("capped_job", max_runs=2, log_dir=log_dir):
            pass
    assert exc_info.value.job_name == "capped_job"
    assert exc_info.value.max_runs == 2
    assert exc_info.value.current == 2


def test_exceeded_error_message_contains_job_name(log_dir):
    increment("named_job", log_dir)
    with pytest.raises(RunCountExceededError) as exc_info:
        with RunCountGuard("named_job", max_runs=1, log_dir=log_dir):
            pass
    assert "named_job" in str(exc_info.value)


def test_guard_does_not_suppress_exceptions(log_dir):
    with pytest.raises(ValueError):
        with RunCountGuard("err_job", max_runs=10, log_dir=log_dir):
            raise ValueError("boom")
