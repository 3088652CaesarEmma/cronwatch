"""Healthcheck endpoint support for cronwatch.

Allows jobs to report liveness via a URL ping (e.g., healthchecks.io,
betteruptime, or a self-hosted endpoint) on success, failure, or start.
"""

from __future__ import annotations

import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthcheckPolicy:
    """Policy for pinging a healthcheck URL after a job run."""

    url: Optional[str] = None
    ping_on_start: bool = False
    ping_on_failure: bool = True
    timeout_seconds: int = 10

    def __post_init__(self) -> None:
        if self.url is not None and not isinstance(self.url, str):
            raise TypeError("url must be a string or None")
        if self.url == "":
            self.url = None
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")

    @property
    def enabled(self) -> bool:
        return self.url is not None

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "HealthcheckPolicy":
        if not cfg:
            return cls()
        return cls(
            url=cfg.get("url"),
            ping_on_start=bool(cfg.get("ping_on_start", False)),
            ping_on_failure=bool(cfg.get("ping_on_failure", True)),
            timeout_seconds=int(cfg.get("timeout_seconds", 10)),
        )


def _ping(url: str, timeout: int) -> bool:
    """Send a GET request to url. Returns True on success."""
    try:
        with urllib.request.urlopen(url, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def ping_start(policy: HealthcheckPolicy) -> bool:
    """Ping the /start endpoint if ping_on_start is enabled."""
    if not policy.enabled or not policy.ping_on_start:
        return False
    url = policy.url.rstrip("/") + "/start"
    return _ping(url, policy.timeout_seconds)


def ping_success(policy: HealthcheckPolicy) -> bool:
    """Ping the base URL to signal a successful run."""
    if not policy.enabled:
        return False
    return _ping(policy.url, policy.timeout_seconds)


def ping_failure(policy: HealthcheckPolicy) -> bool:
    """Ping the /fail endpoint if ping_on_failure is enabled."""
    if not policy.enabled or not policy.ping_on_failure:
        return False
    url = policy.url.rstrip("/") + "/fail"
    return _ping(url, policy.timeout_seconds)
