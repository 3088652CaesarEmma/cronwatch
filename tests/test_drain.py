"""Tests for cronwatch.drain and cronwatch.drain_guard."""
import threading
import time

import pytest

from cronwatch.drain import DrainCoordinator, DrainPolicy
from cronwatch.drain_guard import DrainGuard


# ---------------------------------------------------------------------------
# DrainPolicy
# ---------------------------------------------------------------------------

def test_drain_policy_defaults():
    p = DrainPolicy()
    assert p.timeout == 30.0
    assert p.poll_interval == 0.25


def test_drain_policy_enabled_when_timeout_nonzero():
    assert DrainPolicy(timeout=5).enabled is True


def test_drain_policy_disabled_when_timeout_zero():
    assert DrainPolicy(timeout=0).enabled is False


def test_drain_policy_negative_timeout_raises():
    with pytest.raises(ValueError, match="timeout"):
        DrainPolicy(timeout=-1)


def test_drain_policy_zero_poll_interval_raises():
    with pytest.raises(ValueError, match="poll_interval"):
        DrainPolicy(poll_interval=0)


def test_drain_policy_from_config_none_returns_defaults():
    p = DrainPolicy.from_config(None)
    assert p.timeout == 30.0


def test_drain_policy_from_config_sets_fields():
    p = DrainPolicy.from_config({"timeout": 10, "poll_interval": 0.1})
    assert p.timeout == 10.0
    assert p.poll_interval == 0.1


# ---------------------------------------------------------------------------
# DrainCoordinator
# ---------------------------------------------------------------------------

def test_coordinator_acquire_increments_count():
    c = DrainCoordinator(DrainPolicy())
    c.acquire("job-a")
    assert c.active_count == 1


def test_coordinator_release_decrements_count():
    c = DrainCoordinator(DrainPolicy())
    c.acquire("job-a")
    c.release("job-a")
    assert c.active_count == 0


def test_coordinator_active_jobs_sorted():
    c = DrainCoordinator(DrainPolicy())
    c.acquire("zzz")
    c.acquire("aaa")
    assert c.active_jobs == ["aaa", "zzz"]


def test_drain_returns_true_when_no_active_jobs():
    c = DrainCoordinator(DrainPolicy(timeout=1))
    assert c.drain() is True


def test_drain_waits_for_job_to_finish():
    c = DrainCoordinator(DrainPolicy(timeout=2, poll_interval=0.05))
    c.acquire("slow-job")

    def release_after():
        time.sleep(0.15)
        c.release("slow-job")

    t = threading.Thread(target=release_after)
    t.start()
    result = c.drain()
    t.join()
    assert result is True


def test_drain_returns_false_on_timeout():
    c = DrainCoordinator(DrainPolicy(timeout=0.1, poll_interval=0.02))
    c.acquire("stuck-job")
    assert c.drain() is False


def test_drain_disabled_policy_returns_true_immediately():
    c = DrainCoordinator(DrainPolicy(timeout=0))
    c.acquire("job")
    assert c.drain() is True


# ---------------------------------------------------------------------------
# DrainGuard
# ---------------------------------------------------------------------------

def test_guard_registers_job_on_enter():
    c = DrainCoordinator(DrainPolicy())
    g = DrainGuard(c, "my-job")
    g.__enter__()
    assert "my-job" in c.active_jobs
    g.__exit__(None, None, None)


def test_guard_releases_job_on_exit():
    c = DrainCoordinator(DrainPolicy())
    with DrainGuard(c, "my-job"):
        pass
    assert c.active_count == 0


def test_guard_does_not_suppress_exceptions():
    c = DrainCoordinator(DrainPolicy())
    with pytest.raises(RuntimeError):
        with DrainGuard(c, "bad-job"):
            raise RuntimeError("boom")
    assert c.active_count == 0


def test_guard_returns_self_on_enter():
    c = DrainCoordinator(DrainPolicy())
    g = DrainGuard(c, "j")
    assert g.__enter__() is g
    g.__exit__(None, None, None)
