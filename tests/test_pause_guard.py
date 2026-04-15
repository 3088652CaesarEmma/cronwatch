"""Tests for cronwatch.pause_guard."""

import pytest

from cronwatch.pause import pause_job, resume_job
from cronwatch.pause_guard import JobPausedError, PauseGuard


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def test_guard_allows_when_not_paused(log_dir):
    with PauseGuard("active_job", log_dir=log_dir):
        pass  # should not raise


def test_guard_raises_when_paused(log_dir):
    pause_job("frozen_job", log_dir)
    with pytest.raises(JobPausedError):
        with PauseGuard("frozen_job", log_dir=log_dir):
            pass


def test_guard_allows_after_resume(log_dir):
    pause_job("myjob", log_dir)
    resume_job("myjob", log_dir)
    with PauseGuard("myjob", log_dir=log_dir):
        pass  # should not raise


def test_paused_error_contains_job_name(log_dir):
    pause_job("important_job", log_dir)
    with pytest.raises(JobPausedError) as exc_info:
        with PauseGuard("important_job", log_dir=log_dir):
            pass
    assert exc_info.value.job_name == "important_job"


def test_paused_error_message_contains_job_name(log_dir):
    pause_job("report_job", log_dir)
    with pytest.raises(JobPausedError) as exc_info:
        with PauseGuard("report_job", log_dir=log_dir):
            pass
    assert "report_job" in str(exc_info.value)


def test_guard_does_not_suppress_other_exceptions(log_dir):
    with pytest.raises(ValueError):
        with PauseGuard("active_job", log_dir=log_dir):
            raise ValueError("unrelated error")
