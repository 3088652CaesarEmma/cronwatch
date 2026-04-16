"""Graceful signal handling for cronwatch job execution."""

import signal
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


@dataclass
class SignalHandlerPolicy:
    """Policy for handling OS signals during job execution."""

    graceful_timeout: float = 5.0  # seconds to wait after SIGTERM before SIGKILL
    handle_sigterm: bool = True
    handle_sighup: bool = False

    def __post_init__(self) -> None:
        if self.graceful_timeout < 0:
            raise ValueError("graceful_timeout must be >= 0")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SignalHandlerPolicy":
        if not cfg:
            return cls()
        return cls(
            graceful_timeout=float(cfg.get("graceful_timeout", 5.0)),
            handle_sigterm=bool(cfg.get("handle_sigterm", True)),
            handle_sighup=bool(cfg.get("handle_sighup", False)),
        )


class SignalHandler:
    """Context manager that installs temporary signal handlers for a job run."""

    def __init__(self, policy: SignalHandlerPolicy) -> None:
        self.policy = policy
        self._terminated: bool = False
        self._callbacks: List[Callable[[], None]] = []
        self._original_sigterm: Optional[signal.Handlers] = None
        self._original_sighup: Optional[signal.Handlers] = None

    @property
    def terminated(self) -> bool:
        """True if a termination signal was received."""
        return self._terminated

    def register_callback(self, fn: Callable[[], None]) -> None:
        """Register a callback to invoke when a signal is received."""
        self._callbacks.append(fn)

    def _handle_signal(self, signum: int, frame: object) -> None:
        sig_name = signal.Signals(signum).name
        log.warning("Received signal %s; requesting graceful shutdown", sig_name)
        self._terminated = True
        for cb in self._callbacks:
            try:
                cb()
            except Exception as exc:  # pragma: no cover
                log.debug("Signal callback raised: %s", exc)

    def __enter__(self) -> "SignalHandler":
        if self.policy.handle_sigterm:
            self._original_sigterm = signal.signal(signal.SIGTERM, self._handle_signal)
        if self.policy.handle_sighup:
            self._original_sighup = signal.signal(signal.SIGHUP, self._handle_signal)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self.policy.handle_sigterm and self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)
        if self.policy.handle_sighup and self._original_sighup is not None:
            signal.signal(signal.SIGHUP, self._original_sighup)
