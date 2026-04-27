"""Tests for cronwatch.streak_guard."""
import pytest

from cronwatch.runner import JobResult
from cronwatch.streak import get_streak
from cronwatch.streak_guard import StreakGuard


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _result(cmd: str, exit_code: int) -> JobResult:
    return JobResult(command=cmd, exit_code=exit_code, stdout="", stderr="", duration=0.1)


def test_guard_records_streak_on_exit(log_dir):
    r = _result("myjob", 0)
    with StreakGuard("myjob", log_dir=log_dir) as g:
        g.set_result(r)
    assert g.state is not None
    assert g.state.current == 1


def test_guard_no_result_does_not_raise(log_dir):
    with StreakGuard("myjob", log_dir=log_dir):
        pass  # no set_result call


def test_guard_state_none_when_no_result(log_dir):
    with StreakGuard("myjob", log_dir=log_dir) as g:
        pass
    assert g.state is None


def test_guard_persists_streak(log_dir):
    r = _result("myjob", 0)
    with StreakGuard("myjob", log_dir=log_dir) as g:
        g.set_result(r)
    loaded = get_streak("myjob", log_dir=log_dir)
    assert loaded is not None
    assert loaded.current == 1


def test_guard_does_not_suppress_exceptions(log_dir):
    with pytest.raises(RuntimeError):
        with StreakGuard("myjob", log_dir=log_dir) as g:
            g.set_result(_result("myjob", 0))
            raise RuntimeError("boom")


def test_guard_returns_self_on_enter(log_dir):
    guard = StreakGuard("myjob", log_dir=log_dir)
    with guard as g:
        assert g is guard
