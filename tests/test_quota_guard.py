"""Tests for cronwatch.quota_guard."""

import pytest

from cronwatch.quota import QuotaPolicy, get_quota_state_path, record_quota_run
from cronwatch.quota_guard import QuotaExceededError, QuotaGuard


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


def test_quota_guard_allows_when_under_limit(log_dir):
    policy = QuotaPolicy(max_runs=3, window_seconds=3600)
    with QuotaGuard(policy, log_dir, "job") as guard:
        assert guard is not None  # entered successfully


def test_quota_guard_records_run_on_success(log_dir):
    policy = QuotaPolicy(max_runs=5, window_seconds=3600)
    with QuotaGuard(policy, log_dir, "job"):
        pass
    path = get_quota_state_path(log_dir, "job")
    assert path.exists()


def test_quota_guard_raises_when_quota_exceeded(log_dir):
    policy = QuotaPolicy(max_runs=1, window_seconds=3600)
    record_quota_run(policy, log_dir, "job")  # fill the quota
    with pytest.raises(QuotaExceededError):
        with QuotaGuard(policy, log_dir, "job"):
            pass  # should never reach here


def test_quota_exceeded_error_message(log_dir):
    policy = QuotaPolicy(max_runs=2, window_seconds=60)
    err = QuotaExceededError("myjob", 2, 60)
    assert "myjob" in str(err)
    assert "2" in str(err)
    assert "60" in str(err)


def test_quota_guard_records_run_even_on_inner_exception(log_dir):
    """A non-quota exception inside the block should still record the run."""
    policy = QuotaPolicy(max_runs=5, window_seconds=3600)
    with pytest.raises(RuntimeError):
        with QuotaGuard(policy, log_dir, "job"):
            raise RuntimeError("boom")
    path = get_quota_state_path(log_dir, "job")
    assert path.exists()


def test_quota_guard_disabled_policy_never_blocks(log_dir):
    policy = QuotaPolicy(max_runs=0)  # disabled
    # Run many times — should never raise
    for _ in range(10):
        with QuotaGuard(policy, log_dir, "job"):
            pass


def test_quota_guard_blocks_after_limit_reached(log_dir):
    policy = QuotaPolicy(max_runs=2, window_seconds=3600)
    with QuotaGuard(policy, log_dir, "job"):
        pass
    with QuotaGuard(policy, log_dir, "job"):
        pass
    with pytest.raises(QuotaExceededError):
        with QuotaGuard(policy, log_dir, "job"):
            pass
