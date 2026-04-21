"""Webhook notification policy and delivery for cronwatch."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from cronwatch.runner import JobResult


@dataclass
class WebhookPolicy:
    url: Optional[str] = None
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 10
    on_failure: bool = True
    on_success: bool = False

    def __post_init__(self) -> None:
        if self.url is not None and not isinstance(self.url, str):
            raise TypeError("url must be a string or None")
        if self.url == "":
            self.url = None
        if self.method not in ("POST", "PUT", "PATCH"):
            raise ValueError(f"method must be POST, PUT, or PATCH; got {self.method!r}")
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")

    @property
    def enabled(self) -> bool:
        return self.url is not None

    @classmethod
    def from_config(cls, cfg: Optional[Dict[str, Any]]) -> "WebhookPolicy":
        if not cfg:
            return cls()
        return cls(
            url=cfg.get("url"),
            method=cfg.get("method", "POST"),
            headers=cfg.get("headers", {}),
            timeout=cfg.get("timeout", 10),
            on_failure=cfg.get("on_failure", True),
            on_success=cfg.get("on_success", False),
        )


def build_webhook_payload(result: JobResult) -> Dict[str, Any]:
    """Build the JSON payload sent to the webhook endpoint."""
    return {
        "job": result.command,
        "exit_code": result.exit_code,
        "success": result.exit_code == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration": result.duration,
    }


def send_webhook(result: JobResult, policy: WebhookPolicy) -> bool:
    """Send a webhook notification. Returns True on success, False on error."""
    if not policy.enabled:
        return False
    is_success = result.exit_code == 0
    if is_success and not policy.on_success:
        return False
    if not is_success and not policy.on_failure:
        return False

    payload = build_webhook_payload(result)
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", **policy.headers}
    req = urllib.request.Request(
        policy.url, data=body, headers=headers, method=policy.method
    )
    try:
        with urllib.request.urlopen(req, timeout=policy.timeout):
            return True
    except urllib.error.URLError:
        return False
