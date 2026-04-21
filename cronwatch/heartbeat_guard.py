"""Context manager that starts/stops a HeartbeatThread around a job."""

from __future__ import annotations

from cronwatch.heartbeat import HeartbeatPolicy, HeartbeatThread


class HeartbeatGuard:
    """Start a heartbeat thread on enter, stop it on exit."""

    def __init__(self, policy: HeartbeatPolicy) -> None:
        self._policy = policy
        self._thread = HeartbeatThread(policy)

    def __enter__(self) -> "HeartbeatGuard":
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._thread.stop()
        return False  # do not suppress exceptions
