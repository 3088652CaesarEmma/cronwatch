"""Tests for cronwatch.quota_reset_guard."""
import time
from pathlib import Path

import pytest

from cronwatch.quota import QuotaPolicy, load_quota_state, save_quota_state
from cronwatch.quota_reset import QuotaResetPolicy, load_quota_reset_state
from cronwatch.quota_reset_guard import QuotaResetGuard


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed_quota(job_name: str, runs: list, log_dir: Path) -> None:
    save_quota_state(job_name, {"runs": runs}, log_dir)


def test_guard_disabled_policy_does_not_reset(log_dir):
    reset_policy = QuotaResetPolicy()  # disabled
    quota_policy = QuotaPolicy(max_runs=10, window=3600)
    runs = [time.time()]
    _seed_quota("job1", runs, log_dir)

    with QuotaResetGuard(reset_policy, quota_policy, "job1", log_dir) as g:
        g.set_success(True)

    state = load_quota_state("job1", log_dir)
    assert len(state["runs"]) == 1  # unchanged


def test_guard_resets_on_success_when_policy_set(log_dir):
    reset_policy = QuotaResetPolicy(reset_on_success=True)
    quota_policy = QuotaPolicy(max_runs=10, window=3600)
    _seed_quota("job2", [time.time(), time.time()], log_dir)

    with QuotaResetGuard(reset_policy, quota_policy, "job2", log_dir) as g:
        g.set_success(True)

    state = load_quota_state("job2", log_dir)
    assert state["runs"] == []


def test_guard_does_not_reset_on_failure_when_reset_on_success(log_dir):
    reset_policy = QuotaResetPolicy(reset_on_success=True)
    quota_policy = QuotaPolicy(max_runs=10, window=3600)
    runs = [time.time()]
    _seed_quota("job3", runs, log_dir)

    with QuotaResetGuard(reset_policy, quota_policy, "job3", log_dir) as g:
        g.set_success(False)

    state = load_quota_state("job3", log_dir)
    assert len(state["runs"]) == 1


def test_guard_records_reset_timestamp(log_dir):
    reset_policy = QuotaResetPolicy(reset_on_success=True)
    quota_policy = QuotaPolicy(max_runs=10, window=3600)
    _seed_quota("job4", [], log_dir)

    before = time.time()
    with QuotaResetGuard(reset_policy, quota_policy, "job4", log_dir) as g:
        g.set_success(True)

    rs = load_quota_reset_state("job4", log_dir)
    assert rs.get("last_reset", 0) >= before


def test_guard_does_not_suppress_exceptions(log_dir):
    reset_policy = QuotaResetPolicy(reset_on_success=True)
    quota_policy = QuotaPolicy(max_runs=10, window=3600)
    _seed_quota("job5", [], log_dir)

    with pytest.raises(RuntimeError, match="boom"):
        with QuotaResetGuard(reset_policy, quota_policy, "job5", log_dir) as g:
            g.set_success(True)
            raise RuntimeError("boom")


def test_guard_returns_self_on_enter(log_dir):
    reset_policy = QuotaResetPolicy()
    quota_policy = QuotaPolicy(max_runs=5, window=60)
    guard = QuotaResetGuard(reset_policy, quota_policy, "job6", log_dir)
    assert guard.__enter__() is guard
    guard.__exit__(None, None, None)
