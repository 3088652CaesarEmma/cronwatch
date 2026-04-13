"""Tests for cronwatch.concurrency."""

from __future__ import annotations

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from cronwatch.concurrency import (
    ConcurrencyPolicy,
    get_concurrency_state_path,
    running_count,
    register_running,
    deregister_running,
    can_run,
)


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- ConcurrencyPolicy ---

def test_concurrency_policy_defaults():
    p = ConcurrencyPolicy()
    assert p.max_jobs == 0
    assert not p.enabled


def test_concurrency_policy_enabled_when_nonzero():
    p = ConcurrencyPolicy(max_jobs=3)
    assert p.enabled


def test_concurrency_policy_negative_raises():
    with pytest.raises(ValueError):
        ConcurrencyPolicy(max_jobs=-1)


def test_concurrency_policy_from_config_none():
    p = ConcurrencyPolicy.from_config(None)
    assert p.max_jobs == 0


def test_concurrency_policy_from_config_dict():
    p = ConcurrencyPolicy.from_config({"max_jobs": 4})
    assert p.max_jobs == 4


# --- State path ---

def test_get_concurrency_state_path_uses_log_dir(log_dir):
    path = get_concurrency_state_path(log_dir)
    assert path.parent == log_dir
    assert path.name == "concurrency_state.json"


# --- running_count ---

def test_running_count_empty_when_no_file(log_dir):
    assert running_count(log_dir) == 0


def test_running_count_counts_alive_pids(log_dir):
    state_path = get_concurrency_state_path(log_dir)
    state_path.write_text(json.dumps([
        {"job": "a", "pid": os.getpid(), "started": 0.0},
    ]))
    assert running_count(log_dir) == 1


def test_running_count_prunes_dead_pids(log_dir):
    state_path = get_concurrency_state_path(log_dir)
    state_path.write_text(json.dumps([
        {"job": "dead", "pid": 99999999, "started": 0.0},
    ]))
    assert running_count(log_dir) == 0
    # Pruned entry should be removed from file
    remaining = json.loads(state_path.read_text())
    assert remaining == []


# --- register / deregister ---

def test_register_and_deregister(log_dir):
    register_running("myjob", log_dir)
    assert running_count(log_dir) == 1
    deregister_running(log_dir)
    assert running_count(log_dir) == 0


# --- can_run ---

def test_can_run_unlimited_policy_always_true(log_dir):
    policy = ConcurrencyPolicy(max_jobs=0)
    register_running("job1", log_dir)
    register_running("job2", log_dir)
    assert can_run(policy, log_dir) is True
    deregister_running(log_dir)


def test_can_run_respects_max_jobs(log_dir):
    policy = ConcurrencyPolicy(max_jobs=1)
    assert can_run(policy, log_dir) is True
    register_running("job1", log_dir)
    assert can_run(policy, log_dir) is False
    deregister_running(log_dir)
    assert can_run(policy, log_dir) is True
