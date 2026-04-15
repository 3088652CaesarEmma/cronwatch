"""Tests for cronwatch.cooldown and cronwatch.cooldown_guard."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from cronwatch.cooldown import (
    CooldownPolicy,
    clear_cooldown,
    get_cooldown_state_path,
    is_cooling_down,
    load_cooldown_state,
    record_failure,
    save_cooldown_state,
)
from cronwatch.cooldown_guard import CooldownActiveError, CooldownGuard


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# ── CooldownPolicy ────────────────────────────────────────────────────────────

def test_cooldown_policy_defaults():
    p = CooldownPolicy()
    assert p.seconds == 0
    assert not p.enabled


def test_cooldown_policy_enabled_when_nonzero():
    p = CooldownPolicy(seconds=60)
    assert p.enabled


def test_cooldown_policy_negative_raises():
    with pytest.raises(ValueError):
        CooldownPolicy(seconds=-1)


def test_cooldown_policy_from_config_none_returns_defaults():
    p = CooldownPolicy.from_config(None)
    assert p.seconds == 0


def test_cooldown_policy_from_config_reads_seconds():
    p = CooldownPolicy.from_config({"seconds": 120})
    assert p.seconds == 120


# ── State helpers ─────────────────────────────────────────────────────────────

def test_get_cooldown_state_path_uses_log_dir(log_dir):
    path = get_cooldown_state_path("myjob", log_dir)
    assert str(log_dir) in str(path)
    assert "myjob" in path.name


def test_save_and_load_roundtrip(log_dir):
    save_cooldown_state("job1", {"last_failure": 12345.0}, log_dir)
    state = load_cooldown_state("job1", log_dir)
    assert state["last_failure"] == 12345.0


def test_load_returns_empty_when_no_file(log_dir):
    state = load_cooldown_state("nonexistent", log_dir)
    assert state == {}


def test_record_failure_sets_timestamp(log_dir):
    before = time.time()
    record_failure("job2", log_dir)
    after = time.time()
    state = load_cooldown_state("job2", log_dir)
    assert before <= state["last_failure"] <= after


def test_clear_cooldown_removes_last_failure(log_dir):
    record_failure("job3", log_dir)
    clear_cooldown("job3", log_dir)
    state = load_cooldown_state("job3", log_dir)
    assert "last_failure" not in state


def test_is_cooling_down_false_when_disabled(log_dir):
    record_failure("job4", log_dir)
    assert not is_cooling_down("job4", CooldownPolicy(seconds=0), log_dir)


def test_is_cooling_down_true_within_window(log_dir):
    record_failure("job5", log_dir)
    assert is_cooling_down("job5", CooldownPolicy(seconds=3600), log_dir)


def test_is_cooling_down_false_after_window(log_dir):
    save_cooldown_state("job6", {"last_failure": time.time() - 7200}, log_dir)
    assert not is_cooling_down("job6", CooldownPolicy(seconds=60), log_dir)


# ── CooldownGuard ─────────────────────────────────────────────────────────────

def test_guard_allows_when_no_prior_failure(log_dir):
    policy = CooldownPolicy(seconds=300)
    with CooldownGuard("clean_job", policy, log_dir):
        pass  # should not raise


def test_guard_raises_when_cooling_down(log_dir):
    record_failure("hot_job", log_dir)
    policy = CooldownPolicy(seconds=3600)
    with pytest.raises(CooldownActiveError) as exc_info:
        with CooldownGuard("hot_job", policy, log_dir):
            pass
    assert "hot_job" in str(exc_info.value)


def test_guard_disabled_policy_always_passes(log_dir):
    record_failure("any_job", log_dir)
    policy = CooldownPolicy(seconds=0)
    with CooldownGuard("any_job", policy, log_dir):
        pass  # disabled policy must not raise


def test_cooldown_active_error_contains_remaining():
    err = CooldownActiveError("myjob", 42.5)
    assert "42.5" in str(err)
    assert err.seconds_remaining == 42.5
