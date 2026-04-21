"""Tests for cronwatch.heartbeat."""

import time
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.heartbeat import HeartbeatPolicy, HeartbeatThread


# ---------------------------------------------------------------------------
# HeartbeatPolicy
# ---------------------------------------------------------------------------

def test_heartbeat_policy_defaults():
    p = HeartbeatPolicy()
    assert p.url is None
    assert p.interval == 30
    assert p.timeout == 5
    assert p.enabled is False


def test_heartbeat_policy_enabled_when_url_set():
    p = HeartbeatPolicy(url="https://hc-ping.example.com/abc")
    assert p.enabled is True


def test_heartbeat_policy_empty_string_url_becomes_none():
    p = HeartbeatPolicy(url="")
    assert p.url is None
    assert p.enabled is False


def test_heartbeat_policy_invalid_url_type_raises():
    with pytest.raises(TypeError):
        HeartbeatPolicy(url=12345)


def test_heartbeat_policy_invalid_interval_raises():
    with pytest.raises(ValueError):
        HeartbeatPolicy(url="https://example.com", interval=0)


def test_heartbeat_policy_negative_interval_raises():
    with pytest.raises(ValueError):
        HeartbeatPolicy(url="https://example.com", interval=-5)


def test_heartbeat_policy_invalid_timeout_raises():
    with pytest.raises(ValueError):
        HeartbeatPolicy(url="https://example.com", timeout=0)


def test_heartbeat_policy_from_config_none_returns_defaults():
    p = HeartbeatPolicy.from_config(None)
    assert p.url is None
    assert p.interval == 30


def test_heartbeat_policy_from_config_sets_values():
    p = HeartbeatPolicy.from_config({"url": "https://hc.example.com", "interval": 10, "timeout": 3})
    assert p.url == "https://hc.example.com"
    assert p.interval == 10
    assert p.timeout == 3


# ---------------------------------------------------------------------------
# HeartbeatThread
# ---------------------------------------------------------------------------

def test_heartbeat_thread_does_not_start_when_disabled():
    policy = HeartbeatPolicy()  # no url
    ht = HeartbeatThread(policy)
    ht.start()
    assert ht._thread is None
    ht.stop()


def test_heartbeat_thread_pings_url():
    policy = HeartbeatPolicy(url="https://hc.example.com/ping", interval=1)
    with patch("cronwatch.heartbeat.requests.get") as mock_get:
        ht = HeartbeatThread(policy)
        ht.start()
        time.sleep(1.5)
        ht.stop()
        assert mock_get.call_count >= 1
        mock_get.assert_called_with("https://hc.example.com/ping", timeout=5)


def test_heartbeat_thread_swallows_request_errors():
    policy = HeartbeatPolicy(url="https://hc.example.com/ping", interval=1)
    with patch("cronwatch.heartbeat.requests.get", side_effect=Exception("network error")):
        ht = HeartbeatThread(policy)
        ht.start()
        time.sleep(1.5)
        ht.stop()  # should not raise


def test_heartbeat_thread_stops_cleanly():
    policy = HeartbeatPolicy(url="https://hc.example.com/ping", interval=60)
    with patch("cronwatch.heartbeat.requests.get"):
        ht = HeartbeatThread(policy)
        ht.start()
        assert ht._thread is not None
        ht.stop()
        assert ht._thread is None
