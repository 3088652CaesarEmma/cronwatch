"""Heartbeat policy — periodically ping a URL to signal a job is still alive."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional

import requests


@dataclass
class HeartbeatPolicy:
    """Configuration for in-progress heartbeat pings."""

    url: Optional[str] = None
    interval: int = 30  # seconds between pings
    timeout: int = 5    # HTTP request timeout in seconds

    def __post_init__(self) -> None:
        if self.url is not None and not isinstance(self.url, str):
            raise TypeError("heartbeat url must be a string")
        if self.url == "":
            self.url = None
        if not isinstance(self.interval, int) or self.interval <= 0:
            raise ValueError("heartbeat interval must be a positive integer")
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("heartbeat timeout must be a positive integer")

    @property
    def enabled(self) -> bool:
        return self.url is not None

    @classmethod
    def from_config(cls, data: Optional[dict]) -> "HeartbeatPolicy":
        if not data:
            return cls()
        return cls(
            url=data.get("url"),
            interval=data.get("interval", 30),
            timeout=data.get("timeout", 5),
        )

    def _ping(self) -> None:
        try:
            requests.get(self.url, timeout=self.timeout)
        except Exception:
            pass


class HeartbeatThread:
    """Background thread that pings the heartbeat URL at a fixed interval."""

    def __init__(self, policy: HeartbeatPolicy) -> None:
        self._policy = policy
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self._policy.enabled:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._policy.timeout + 1)
            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(timeout=self._policy.interval):
            self._policy._ping()
