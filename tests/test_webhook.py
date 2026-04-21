"""Tests for cronwatch.webhook."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from cronwatch.runner import JobResult
from cronwatch.webhook import WebhookPolicy, build_webhook_payload, send_webhook


@pytest.fixture
def failed_result():
    return JobResult(command="/bin/fail", exit_code=1, stdout="", stderr="error", duration=0.5)


@pytest.fixture
def success_result():
    return JobResult(command="/bin/ok", exit_code=0, stdout="done", stderr="", duration=1.0)


def test_webhook_policy_defaults():
    p = WebhookPolicy()
    assert p.url is None
    assert p.method == "POST"
    assert p.timeout == 10
    assert p.on_failure is True
    assert p.on_success is False
    assert p.enabled is False


def test_webhook_policy_enabled_when_url_set():
    p = WebhookPolicy(url="https://example.com/hook")
    assert p.enabled is True


def test_webhook_policy_empty_string_url_becomes_none():
    p = WebhookPolicy(url="")
    assert p.url is None
    assert p.enabled is False


def test_webhook_policy_invalid_method_raises():
    with pytest.raises(ValueError, match="method"):
        WebhookPolicy(url="https://example.com", method="GET")


def test_webhook_policy_invalid_timeout_raises():
    with pytest.raises(ValueError, match="timeout"):
        WebhookPolicy(url="https://example.com", timeout=0)


def test_from_config_none_returns_defaults():
    p = WebhookPolicy.from_config(None)
    assert p.url is None


def test_from_config_sets_url():
    p = WebhookPolicy.from_config({"url": "https://hooks.example.com"})
    assert p.url == "https://hooks.example.com"


def test_build_webhook_payload_failure(failed_result):
    payload = build_webhook_payload(failed_result)
    assert payload["exit_code"] == 1
    assert payload["success"] is False
    assert payload["job"] == "/bin/fail"
    assert payload["stderr"] == "error"


def test_build_webhook_payload_success(success_result):
    payload = build_webhook_payload(success_result)
    assert payload["success"] is True
    assert payload["stdout"] == "done"


def test_send_webhook_disabled_returns_false(failed_result):
    policy = WebhookPolicy()
    assert send_webhook(failed_result, policy) is False


def test_send_webhook_success_not_sent_by_default(success_result):
    policy = WebhookPolicy(url="https://example.com/hook")
    assert send_webhook(success_result, policy) is False


def test_send_webhook_on_failure_calls_urlopen(failed_result):
    policy = WebhookPolicy(url="https://example.com/hook")
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_ctx) as mock_open:
        result = send_webhook(failed_result, policy)
    assert result is True
    mock_open.assert_called_once()


def test_send_webhook_url_error_returns_false(failed_result):
    import urllib.error
    policy = WebhookPolicy(url="https://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = send_webhook(failed_result, policy)
    assert result is False
