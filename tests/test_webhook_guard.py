"""Tests for cronwatch.webhook_guard."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from cronwatch.runner import JobResult
from cronwatch.webhook import WebhookPolicy
from cronwatch.webhook_guard import WebhookGuard


@pytest.fixture
def failed_result():
    return JobResult(command="/bin/fail", exit_code=1, stdout="", stderr="err", duration=0.1)


def test_guard_fires_webhook_on_exit(failed_result):
    policy = WebhookPolicy(url="https://example.com/hook")
    with patch("cronwatch.webhook_guard.send_webhook") as mock_send:
        with WebhookGuard(policy) as guard:
            guard.result = failed_result
    mock_send.assert_called_once_with(failed_result, policy)


def test_guard_skips_webhook_when_no_result():
    policy = WebhookPolicy(url="https://example.com/hook")
    with patch("cronwatch.webhook_guard.send_webhook") as mock_send:
        with WebhookGuard(policy):
            pass
    mock_send.assert_not_called()


def test_guard_skips_webhook_when_policy_disabled(failed_result):
    policy = WebhookPolicy()  # no url
    with patch("cronwatch.webhook_guard.send_webhook") as mock_send:
        with WebhookGuard(policy) as guard:
            guard.result = failed_result
    mock_send.assert_not_called()


def test_guard_does_not_suppress_exceptions(failed_result):
    policy = WebhookPolicy(url="https://example.com/hook")
    with patch("cronwatch.webhook_guard.send_webhook"):
        with pytest.raises(RuntimeError):
            with WebhookGuard(policy) as guard:
                guard.result = failed_result
                raise RuntimeError("boom")


def test_guard_returns_self_on_enter():
    policy = WebhookPolicy()
    guard = WebhookGuard(policy)
    assert guard.__enter__() is guard
