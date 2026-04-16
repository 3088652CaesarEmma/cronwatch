"""Tests for cronwatch.signal_handler."""

import signal
import pytest
from cronwatch.signal_handler import SignalHandlerPolicy, SignalHandler


# ---------------------------------------------------------------------------
# SignalHandlerPolicy
# ---------------------------------------------------------------------------

def test_signal_handler_policy_defaults():
    policy = SignalHandlerPolicy()
    assert policy.graceful_timeout == 5.0
    assert policy.handle_sigterm is True
    assert policy.handle_sighup is False


def test_signal_handler_policy_negative_timeout_raises():
    with pytest.raises(ValueError, match="graceful_timeout"):
        SignalHandlerPolicy(graceful_timeout=-1.0)


def test_signal_handler_policy_zero_timeout_allowed():
    policy = SignalHandlerPolicy(graceful_timeout=0.0)
    assert policy.graceful_timeout == 0.0


def test_from_config_none_returns_defaults():
    policy = SignalHandlerPolicy.from_config(None)
    assert policy.graceful_timeout == 5.0
    assert policy.handle_sigterm is True


def test_from_config_empty_dict_returns_defaults():
    policy = SignalHandlerPolicy.from_config({})
    assert policy.graceful_timeout == 5.0


def test_from_config_custom_values():
    policy = SignalHandlerPolicy.from_config(
        {"graceful_timeout": 10.0, "handle_sigterm": False, "handle_sighup": True}
    )
    assert policy.graceful_timeout == 10.0
    assert policy.handle_sigterm is False
    assert policy.handle_sighup is True


# ---------------------------------------------------------------------------
# SignalHandler
# ---------------------------------------------------------------------------

def test_signal_handler_context_manager_restores_sigterm():
    original = signal.getsignal(signal.SIGTERM)
    policy = SignalHandlerPolicy(handle_sigterm=True, handle_sighup=False)
    with SignalHandler(policy) as handler:
        installed = signal.getsignal(signal.SIGTERM)
        assert installed == handler._handle_signal
    assert signal.getsignal(signal.SIGTERM) == original


def test_signal_handler_terminated_false_initially():
    policy = SignalHandlerPolicy()
    handler = SignalHandler(policy)
    assert handler.terminated is False


def test_signal_handler_terminated_after_signal():
    policy = SignalHandlerPolicy(handle_sigterm=True)
    with SignalHandler(policy) as handler:
        assert not handler.terminated
        signal.raise_signal(signal.SIGTERM)
        assert handler.terminated


def test_signal_handler_callback_invoked_on_signal():
    called = []
    policy = SignalHandlerPolicy(handle_sigterm=True)
    with SignalHandler(policy) as handler:
        handler.register_callback(lambda: called.append(True))
        signal.raise_signal(signal.SIGTERM)
    assert called == [True]


def test_signal_handler_multiple_callbacks():
    log = []
    policy = SignalHandlerPolicy(handle_sigterm=True)
    with SignalHandler(policy) as handler:
        handler.register_callback(lambda: log.append("a"))
        handler.register_callback(lambda: log.append("b"))
        signal.raise_signal(signal.SIGTERM)
    assert log == ["a", "b"]


def test_signal_handler_disabled_sigterm_does_not_install():
    original = signal.getsignal(signal.SIGTERM)
    policy = SignalHandlerPolicy(handle_sigterm=False, handle_sighup=False)
    with SignalHandler(policy):
        assert signal.getsignal(signal.SIGTERM) == original
