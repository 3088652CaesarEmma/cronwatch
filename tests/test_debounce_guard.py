"""Tests for cronwatch.debounce_guard."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from cronwatch.debounce import DebouncePolicy, load_debounce_state, save_debounce_state
from cronwatch.debounce_guard import DebounceGuard


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_guard_not_suppressed_when_policy_disabled(log_dir):
    policy = DebouncePolicy(window_seconds=0)
    with DebounceGuard(policy, "job", log_dir) as g:
        pass
    assert not g.suppressed


def test_guard_not_suppressed_on_first_run(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    with DebounceGuard(policy, "job", log_dir) as g:
        pass
    assert not g.suppressed


def test_guard_records_fired_after_successful_block(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    with DebounceGuard(policy, "job", log_dir):
        pass
    state = load_debounce_state("job", log_dir)
    assert "last_fired" in state


def test_guard_suppressed_within_window(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    save_debounce_state("job", {"last_fired": time.time()}, log_dir)
    with DebounceGuard(policy, "job", log_dir) as g:
        pass
    assert g.suppressed


def test_guard_not_suppressed_after_window_expires(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    save_debounce_state("job", {"last_fired": time.time() - 120}, log_dir)
    with DebounceGuard(policy, "job", log_dir) as g:
        pass
    assert not g.suppressed


def test_guard_does_not_suppress_exceptions(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    with pytest.raises(RuntimeError):
        with DebounceGuard(policy, "job", log_dir):
            raise RuntimeError("boom")


def test_guard_does_not_record_fired_when_exception_raised(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    try:
        with DebounceGuard(policy, "job", log_dir):
            raise ValueError("fail")
    except ValueError:
        pass
    state = load_debounce_state("job", log_dir)
    assert "last_fired" not in state
