"""Tests for cronwatch configuration loader."""

import os
import tempfile
import textwrap
import pytest

from cronwatch.config import load_config, CronwatchConfig, EmailConfig, SlackConfig


SAMPLE_CONFIG = textwrap.dedent("""
    log_dir: /tmp/cronwatch_logs
    log_level: DEBUG
    retention_days: 7

    email:
      enabled: true
      smtp_host: mail.example.com
      smtp_port: 465
      smtp_user: user@example.com
      smtp_password: secret
      from_address: noreply@example.com
      to_addresses:
        - ops@example.com
        - dev@example.com
      use_tls: true

    slack:
      enabled: true
      webhook_url: https://hooks.slack.com/services/A/B/C
      channel: "#alerts"
""")


@pytest.fixture
def config_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(SAMPLE_CONFIG)
        path = f.name
    yield path
    os.unlink(path)


def test_load_config_from_file(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg, CronwatchConfig)
    assert cfg.log_dir == "/tmp/cronwatch_logs"
    assert cfg.log_level == "DEBUG"
    assert cfg.retention_days == 7


def test_email_config_loaded(config_file):
    cfg = load_config(config_file)
    assert cfg.email.enabled is True
    assert cfg.email.smtp_host == "mail.example.com"
    assert cfg.email.smtp_port == 465
    assert cfg.email.to_addresses == ["ops@example.com", "dev@example.com"]


def test_slack_config_loaded(config_file):
    cfg = load_config(config_file)
    assert cfg.slack.enabled is True
    assert cfg.slack.webhook_url == "https://hooks.slack.com/services/A/B/C"
    assert cfg.slack.channel == "#alerts"


def test_defaults_when_no_file():
    cfg = load_config("/nonexistent/path/config.yml")
    assert cfg.log_dir == "/var/log/cronwatch"
    assert cfg.log_level == "INFO"
    assert cfg.retention_days == 30
    assert cfg.email.enabled is False
    assert cfg.slack.enabled is False


def test_env_var_config_path(config_file, monkeypatch):
    monkeypatch.setenv("CRONWATCH_CONFIG", config_file)
    cfg = load_config()
    assert cfg.log_level == "DEBUG"
