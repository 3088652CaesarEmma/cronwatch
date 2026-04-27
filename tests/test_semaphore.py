"""Tests for cronwatch.semaphore."""
import json
import os

import pytest

from cronwatch.semaphore import (
    SemaphorePolicy,
    acquire_semaphore,
    get_semaphore_path,
    release_semaphore,
)


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


# --- SemaphorePolicy ---

def test_semaphore_policy_defaults():
    p = SemaphorePolicy()
    assert p.name == ""
    assert p.slots == 1
    assert p.enabled is False


def test_semaphore_policy_enabled_when_name_set():
    p = SemaphorePolicy(name="db-jobs")
    assert p.enabled is True


def test_semaphore_policy_invalid_slots_type_raises():
    with pytest.raises(TypeError):
        SemaphorePolicy(name="x", slots="3")  # type: ignore


def test_semaphore_policy_zero_slots_raises():
    with pytest.raises(ValueError):
        SemaphorePolicy(name="x", slots=0)


def test_semaphore_policy_negative_slots_raises():
    with pytest.raises(ValueError):
        SemaphorePolicy(name="x", slots=-1)


def test_semaphore_policy_from_config_none_returns_defaults():
    p = SemaphorePolicy.from_config(None)
    assert p.name == ""
    assert p.slots == 1


def test_semaphore_policy_from_config_sets_fields():
    p = SemaphorePolicy.from_config({"name": "my-sem", "slots": 4})
    assert p.name == "my-sem"
    assert p.slots == 4


# --- get_semaphore_path ---

def test_get_semaphore_path_uses_log_dir(log_dir):
    p = get_semaphore_path("my-sem", log_dir=log_dir)
    assert str(p).startswith(log_dir)
    assert "my-sem" in p.name


# --- acquire / release ---

def test_acquire_creates_state_file(log_dir):
    policy = SemaphorePolicy(name="test", slots=2)
    result = acquire_semaphore(policy, "job-a", log_dir=log_dir)
    assert result is True
    path = get_semaphore_path("test", log_dir=log_dir)
    assert path.exists()


def test_acquire_respects_slot_limit(log_dir):
    policy = SemaphorePolicy(name="limited", slots=1)
    # Seed a holder with the current PID so it appears alive
    path = get_semaphore_path("limited", log_dir=log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"job": "other", "pid": os.getpid(), "ts": 0}]))
    result = acquire_semaphore(policy, "job-b", log_dir=log_dir)
    assert result is False


def test_release_removes_own_pid(log_dir):
    policy = SemaphorePolicy(name="rel", slots=3)
    acquire_semaphore(policy, "job-x", log_dir=log_dir)
    release_semaphore(policy, log_dir=log_dir)
    path = get_semaphore_path("rel", log_dir=log_dir)
    holders = json.loads(path.read_text())
    pids = [h["pid"] for h in holders]
    assert os.getpid() not in pids


def test_acquire_cleans_dead_pids(log_dir):
    policy = SemaphorePolicy(name="clean", slots=1)
    path = get_semaphore_path("clean", log_dir=log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    # PID 99999999 is almost certainly dead
    path.write_text(json.dumps([{"job": "ghost", "pid": 99999999, "ts": 0}]))
    result = acquire_semaphore(policy, "job-new", log_dir=log_dir)
    assert result is True
