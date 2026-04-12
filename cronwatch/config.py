"""Configuration loader for cronwatch."""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: list = field(default_factory=list)
    use_tls: bool = True


@dataclass
class SlackConfig:
    enabled: bool = False
    webhook_url: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class CronwatchConfig:
    log_dir: str = "/var/log/cronwatch"
    log_level: str = "INFO"
    retention_days: int = 30
    email: EmailConfig = field(default_factory=EmailConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)


def load_config(config_path: Optional[str] = None) -> CronwatchConfig:
    """Load configuration from a YAML file."""
    search_paths = [
        config_path,
        os.environ.get("CRONWATCH_CONFIG"),
        os.path.expanduser("~/.cronwatch.yml"),
        "/etc/cronwatch/config.yml",
    ]

    raw = {}
    for path in search_paths:
        if path and os.path.isfile(path):
            with open(path, "r") as f:
                raw = yaml.safe_load(f) or {}
            break

    email_data = raw.get("email", {})
    slack_data = raw.get("slack", {})

    return CronwatchConfig(
        log_dir=raw.get("log_dir", "/var/log/cronwatch"),
        log_level=raw.get("log_level", "INFO"),
        retention_days=raw.get("retention_days", 30),
        email=EmailConfig(**{k: v for k, v in email_data.items() if hasattr(EmailConfig, k)}),
        slack=SlackConfig(**{k: v for k, v in slack_data.items() if hasattr(SlackConfig, k)}),
    )
