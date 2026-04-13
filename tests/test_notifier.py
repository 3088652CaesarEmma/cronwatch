"""Tests for cronwatch.notifier module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import CronwatchConfig, EmailConfig, SlackConfig
from cronwatch.runner import JobResult
from cronwatch.notifier import build_email_body, send_email, send_slack, notify


@pytest.fixture
def failed_result():
    return JobResult(
        command="/usr/bin/backup.sh",
        exit_code=1,
        stdout="backing up...",
        stderr="error: disk full",
        duration=3.14,
    )


@pytest.fixture
def success_result():
    return JobResult(
        command="/usr/bin/backup.sh",
        exit_code=0,
        stdout="done",
        stderr="",
        duration=1.0,
    )


@pytest.fixture
def email_config():
    return EmailConfig(
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        use_tls=True,
        username="user@example.com",
        password="secret",
        from_address="user@example.com",
        to_addresses=["admin@example.com"],
    )


@pytest.fixture
def slack_config():
    return SlackConfig(
        enabled=True,
        webhook_url="https://hooks.slack.com/services/TEST/WEBHOOK",
    )


def test_build_email_body_contains_command(failed_result):
    body = build_email_body(failed_result)
    assert "/usr/bin/backup.sh" in body


def test_build_email_body_contains_exit_code(failed_result):
    body = build_email_body(failed_result)
    assert "Exit code: 1" in body


def test_build_email_body_contains_stderr(failed_result):
    body = build_email_body(failed_result)
    assert "error: disk full" in body


def test_send_email_disabled_returns_false(failed_result, email_config):
    email_config.enabled = False
    cfg = CronwatchConfig(email=email_config)
    assert send_email(failed_result, cfg) is False


def test_send_email_success(failed_result, email_config):
    cfg = CronwatchConfig(email=email_config)
    with patch("cronwatch.notifier.smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        result = send_email(failed_result, cfg)
    assert result is True
    instance.sendmail.assert_called_once()


def test_send_email_smtp_error_returns_false(failed_result, email_config):
    import smtplib
    cfg = CronwatchConfig(email=email_config)
    with patch("cronwatch.notifier.smtplib.SMTP", side_effect=smtplib.SMTPException("boom")):
        result = send_email(failed_result, cfg)
    assert result is False


def test_send_slack_disabled_returns_false(failed_result, slack_config):
    slack_config.enabled = False
    cfg = CronwatchConfig(slack=slack_config)
    assert send_slack(failed_result, cfg) is False


def test_send_slack_success(failed_result, slack_config):
    cfg = CronwatchConfig(slack=slack_config)
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifier.urllib.request.urlopen", return_value=mock_response):
        result = send_slack(failed_result, cfg)
    assert result is True


def test_notify_skips_on_success(success_result):
    cfg = CronwatchConfig()
    with patch("cronwatch.notifier.send_email") as mock_email, \
         patch("cronwatch.notifier.send_slack") as mock_slack:
        notify(success_result, cfg)
    mock_email.assert_not_called()
    mock_slack.assert_not_called()


def test_notify_calls_both_on_failure(failed_result, email_config, slack_config):
    cfg = CronwatchConfig(email=email_config, slack=slack_config)
    with patch("cronwatch.notifier.send_email") as mock_email, \
         patch("cronwatch.notifier.send_slack") as mock_slack:
        notify(failed_result, cfg)
    mock_email.assert_called_once_with(failed_result, cfg)
    mock_slack.assert_called_once_with(failed_result, cfg)
