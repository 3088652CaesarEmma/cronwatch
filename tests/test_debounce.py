"""Tests for cronwatch.debounce."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwatch.debounce import (
    DebouncePolicy,
    get_debounce_state_path,
    load_debounce_state,
    record_fired,
    save_debounce_state,
    should_debounce,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- DebouncePolicy ---

def test_debounce_policy_defaults():
    p = DebouncePolicy()
    assert p.window_seconds == 0
    assert not p.enabled


def test_debounce_policy_enabled_when_nonzero():
    p = DebouncePolicy(window_seconds=60)
    assert p.enabled


def test_debounce_policy_negative_raises():
    with pytest.raises(ValueError):
        DebouncePolicy(window_seconds=-1)


def test_debounce_policy_zero_disables():
    p = DebouncePolicy(window_seconds=0)
    assert not p.enabled


def test_from_config_none_returns_defaults():
    p = DebouncePolicy.from_config(None)
    assert p.window_seconds == 0


def test_from_config_empty_dict_returns_defaults():
    p = DebouncePolicy.from_config({})
    assert p.window_seconds == 0


def test_from_config_sets_window():
    p = DebouncePolicy.from_config({"window_seconds": 120})
    assert p.window_seconds == 120


# --- State helpers ---

def test_get_debounce_state_path_uses_log_dir(log_dir):
    path = get_debounce_state_path("myjob", log_dir)
    assert str(log_dir) in str(path)
    assert "myjob" in path.name


def test_load_debounce_state_returns_empty_when_no_file(log_dir):
    state = load_debounce_state("nojob", log_dir)
    assert state == {}


def test_save_and_load_roundtrip(log_dir):
    save_debounce_state("job1", {"last_fired": 12345.0}, log_dir)
    state = load_debounce_state("job1", log_dir)
    assert state["last_fired"] == 12345.0


# --- should_debounce ---

def test_should_debounce_disabled_policy_returns_false(log_dir):
    policy = DebouncePolicy(window_seconds=0)
    assert not should_debounce(policy, "job", log_dir)


def test_should_debounce_no_prior_state_returns_false(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    assert not should_debounce(policy, "newjob", log_dir)


def test_should_debounce_recent_fire_returns_true(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    save_debounce_state("job", {"last_fired": time.time()}, log_dir)
    assert should_debounce(policy, "job", log_dir)


def test_should_debounce_old_fire_returns_false(log_dir):
    policy = DebouncePolicy(window_seconds=60)
    save_debounce_state("job", {"last_fired": time.time() - 120}, log_dir)
    assert not should_debounce(policy, "job", log_dir)


def test_record_fired_creates_state(log_dir):
    record_fired("job", log_dir)
    state = load_debounce_state("job", log_dir)
    assert "last_fired" in state
    assert state["last_fired"] <= time.time()
