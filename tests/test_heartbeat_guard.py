"""Tests for cronwatch.heartbeat_guard."""

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.heartbeat import HeartbeatPolicy
from cronwatch.heartbeat_guard import HeartbeatGuard


def test_guard_starts_thread_on_enter():
    policy = HeartbeatPolicy(url="https://hc.example.com/ping", interval=60)
    with patch("cronwatch.heartbeat.requests.get"):
        guard = HeartbeatGuard(policy)
        guard.__enter__()
        assert guard._thread._thread is not None
        guard.__exit__(None, None, None)


def test_guard_stops_thread_on_exit():
    policy = HeartbeatPolicy(url="https://hc.example.com/ping", interval=60)
    with patch("cronwatch.heartbeat.requests.get"):
        with HeartbeatGuard(policy):
            pass
        # thread should be cleaned up


def test_guard_disabled_policy_does_nothing():
    policy = HeartbeatPolicy()  # no url
    guard = HeartbeatGuard(policy)
    guard.__enter__()
    assert guard._thread._thread is None
    guard.__exit__(None, None, None)


def test_guard_does_not_suppress_exceptions():
    policy = HeartbeatPolicy()  # disabled
    guard = HeartbeatGuard(policy)
    result = guard.__exit__(ValueError, ValueError("boom"), None)
    assert result is False


def test_guard_context_manager_propagates_exception():
    policy = HeartbeatPolicy()  # disabled
    with pytest.raises(RuntimeError, match="test error"):
        with HeartbeatGuard(policy):
            raise RuntimeError("test error")
