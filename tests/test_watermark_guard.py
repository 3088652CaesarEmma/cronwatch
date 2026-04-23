"""Tests for cronwatch.watermark_guard."""
import pytest

from cronwatch.watermark import WatermarkPolicy, load_watermarks
from cronwatch.watermark_guard import WatermarkGuard
from cronwatch.runner import JobResult


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _result(command="job.sh", duration=4.0, stdout="done", stderr=""):
    return JobResult(
        command=command,
        exit_code=0,
        stdout=stdout,
        stderr=stderr,
        duration=duration,
    )


def test_guard_disabled_policy_does_nothing(log_dir):
    policy = WatermarkPolicy(enabled=False)
    with WatermarkGuard(policy, log_dir=log_dir) as guard:
        guard.set_result(_result())
    marks = load_watermarks("job.sh", log_dir)
    assert marks == {}


def test_guard_records_watermarks_on_exit(log_dir):
    policy = WatermarkPolicy(enabled=True)
    with WatermarkGuard(policy, log_dir=log_dir) as guard:
        guard.set_result(_result(duration=6.5))
    marks = load_watermarks("job.sh", log_dir)
    assert "duration" in marks
    assert marks["duration"] == pytest.approx(6.5)


def test_guard_skips_update_when_no_result_set(log_dir):
    policy = WatermarkPolicy(enabled=True)
    with WatermarkGuard(policy, log_dir=log_dir):
        pass  # no set_result called
    marks = load_watermarks("job.sh", log_dir)
    assert marks == {}


def test_guard_does_not_suppress_exceptions(log_dir):
    policy = WatermarkPolicy(enabled=True)
    with pytest.raises(RuntimeError):
        with WatermarkGuard(policy, log_dir=log_dir) as guard:
            guard.set_result(_result())
            raise RuntimeError("boom")


def test_guard_returns_self_on_enter(log_dir):
    policy = WatermarkPolicy(enabled=True)
    guard = WatermarkGuard(policy, log_dir=log_dir)
    result = guard.__enter__()
    assert result is guard
    guard.__exit__(None, None, None)


def test_guard_exit_returns_false(log_dir):
    policy = WatermarkPolicy(enabled=True)
    with WatermarkGuard(policy, log_dir=log_dir) as guard:
        guard.set_result(_result())
        ret = guard.__exit__(None, None, None)
    assert ret is False
