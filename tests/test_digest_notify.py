"""Tests for cronwatch.digest_notify module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.digest import DigestPolicy, save_digest_state
from cronwatch.digest_notify import (
    _format_digest_email,
    _format_digest_slack,
    send_digest,
)
from cronwatch.summary import RunSummary


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def mock_result():
    r = MagicMock()
    r.exit_code = 0
    r.command = "echo hello"
    return r


@pytest.fixture
def summary(mock_result):
    s = RunSummary()
    s.add(mock_result)
    return s


def test_format_digest_email_contains_totals(summary):
    body = _format_digest_email(summary)
    assert "Total jobs run" in body
    assert "Succeeded" in body
    assert "Failed" in body


def test_format_digest_email_lists_commands(summary):
    body = _format_digest_email(summary)
    assert "echo hello" in body


def test_format_digest_slack_success(summary):
    text = _format_digest_slack(summary)
    assert "Cronwatch Digest" in text
    assert ":white_check_mark:" in text


def test_format_digest_slack_failure():
    r = MagicMock()
    r.exit_code = 1
    r.command = "false"
    s = RunSummary()
    s.add(r)
    text = _format_digest_slack(s)
    assert ":x:" in text


@patch("cronwatch.digest_notify.build_digest")
@patch("cronwatch.digest_notify.is_digest_due", return_value=True)
@patch("cronwatch.digest_notify.send_email")
@patch("cronwatch.digest_notify.send_slack")
@patch("cronwatch.digest_notify.mark_digest_sent")
def test_send_digest_calls_email_and_slack(
    mock_mark, mock_slack, mock_email, mock_due, mock_build, log_dir, summary
):
    mock_build.return_value = summary
    email_cfg = MagicMock(enabled=True)
    slack_cfg = MagicMock(enabled=True)
    config = MagicMock(email=email_cfg, slack=slack_cfg)
    policy = DigestPolicy(enabled=True)

    result = send_digest(config, ["job1"], policy, log_dir=log_dir)

    assert result is True
    mock_email.assert_called_once()
    mock_slack.assert_called_once()
    mock_mark.assert_called_once()


@patch("cronwatch.digest_notify.is_digest_due", return_value=False)
def test_send_digest_skips_when_not_due(mock_due, log_dir):
    config = MagicMock()
    policy = DigestPolicy(enabled=True)
    result = send_digest(config, ["job1"], policy, log_dir=log_dir)
    assert result is False


@patch("cronwatch.digest_notify.build_digest", return_value=None)
@patch("cronwatch.digest_notify.is_digest_due", return_value=True)
def test_send_digest_skips_when_no_summary(mock_due, mock_build, log_dir):
    config = MagicMock()
    policy = DigestPolicy(enabled=True, only_on_failure=True)
    result = send_digest(config, ["job1"], policy, log_dir=log_dir)
    assert result is False
