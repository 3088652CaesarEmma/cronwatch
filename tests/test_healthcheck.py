"""Tests for cronwatch.healthcheck."""

from unittest.mock import patch, MagicMock
import urllib.error
import pytest

from cronwatch.healthcheck import (
    HealthcheckPolicy,
    ping_start,
    ping_success,
    ping_failure,
    _ping,
)


# ---------------------------------------------------------------------------
# HealthcheckPolicy construction
# ---------------------------------------------------------------------------

def test_healthcheck_policy_defaults():
    p = HealthcheckPolicy()
    assert p.url is None
    assert p.ping_on_start is False
    assert p.ping_on_failure is True
    assert p.timeout_seconds == 10
    assert p.enabled is False


def test_healthcheck_policy_enabled_when_url_set():
    p = HealthcheckPolicy(url="https://hc-ping.example.com/abc123")
    assert p.enabled is True


def test_healthcheck_policy_empty_string_url_becomes_none():
    p = HealthcheckPolicy(url="")
    assert p.url is None
    assert p.enabled is False


def test_healthcheck_policy_invalid_timeout_raises():
    with pytest.raises(ValueError):
        HealthcheckPolicy(url="https://example.com", timeout_seconds=0)


def test_healthcheck_policy_negative_timeout_raises():
    with pytest.raises(ValueError):
        HealthcheckPolicy(url="https://example.com", timeout_seconds=-5)


def test_healthcheck_policy_from_config_none_returns_defaults():
    p = HealthcheckPolicy.from_config(None)
    assert p.url is None
    assert p.enabled is False


def test_healthcheck_policy_from_config_empty_dict_returns_defaults():
    p = HealthcheckPolicy.from_config({})
    assert p.url is None


def test_healthcheck_policy_from_config_full():
    cfg = {
        "url": "https://hc-ping.example.com/xyz",
        "ping_on_start": True,
        "ping_on_failure": False,
        "timeout_seconds": 5,
    }
    p = HealthcheckPolicy.from_config(cfg)
    assert p.url == "https://hc-ping.example.com/xyz"
    assert p.ping_on_start is True
    assert p.ping_on_failure is False
    assert p.timeout_seconds == 5


# ---------------------------------------------------------------------------
# _ping helper
# ---------------------------------------------------------------------------

def test_ping_returns_true_on_success():
    with patch("cronwatch.healthcheck.urllib.request.urlopen") as mock_open:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        result = _ping("https://example.com", 5)
    assert result is True


def test_ping_returns_false_on_url_error():
    with patch("cronwatch.healthcheck.urllib.request.urlopen",
               side_effect=urllib.error.URLError("timeout")):
        result = _ping("https://example.com", 5)
    assert result is False


# ---------------------------------------------------------------------------
# ping_start / ping_success / ping_failure
# ---------------------------------------------------------------------------

def test_ping_start_disabled_policy_returns_false():
    p = HealthcheckPolicy()
    assert ping_start(p) is False


def test_ping_start_calls_start_suffix():
    p = HealthcheckPolicy(url="https://hc.example.com/abc", ping_on_start=True)
    with patch("cronwatch.healthcheck._ping", return_value=True) as mock_ping:
        ping_start(p)
    mock_ping.assert_called_once_with("https://hc.example.com/abc/start", 10)


def test_ping_success_disabled_policy_returns_false():
    p = HealthcheckPolicy()
    assert ping_success(p) is False


def test_ping_success_calls_base_url():
    p = HealthcheckPolicy(url="https://hc.example.com/abc")
    with patch("cronwatch.healthcheck._ping", return_value=True) as mock_ping:
        ping_success(p)
    mock_ping.assert_called_once_with("https://hc.example.com/abc", 10)


def test_ping_failure_disabled_policy_returns_false():
    p = HealthcheckPolicy()
    assert ping_failure(p) is False


def test_ping_failure_calls_fail_suffix():
    p = HealthcheckPolicy(url="https://hc.example.com/abc")
    with patch("cronwatch.healthcheck._ping", return_value=True) as mock_ping:
        ping_failure(p)
    mock_ping.assert_called_once_with("https://hc.example.com/abc/fail", 10)


def test_ping_failure_skipped_when_disabled():
    p = HealthcheckPolicy(url="https://hc.example.com/abc", ping_on_failure=False)
    with patch("cronwatch.healthcheck._ping") as mock_ping:
        result = ping_failure(p)
    assert result is False
    mock_ping.assert_not_called()
