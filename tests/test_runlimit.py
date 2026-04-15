"""Tests for cronwatch.runlimit."""
from __future__ import annotations

import json
import os
import time

import pytest

from cronwatch.runlimit import (
    RunLimitPolicy,
    check_run_limit,
    get_runlimit_state_path,
    record_run,
)


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


# --- RunLimitPolicy ---

def test_runlimit_policy_defaults():
    p = RunLimitPolicy()
    assert p.max_runs == 0
    assert p.window_seconds == 3600
    assert not p.enabled


def test_runlimit_policy_enabled_when_nonzero():
    p = RunLimitPolicy(max_runs=5)
    assert p.enabled


def test_runlimit_policy_negative_max_runs_raises():
    with pytest.raises(ValueError, match="max_runs"):
        RunLimitPolicy(max_runs=-1)


def test_runlimit_policy_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        RunLimitPolicy(max_runs=1, window_seconds=0)


def test_runlimit_policy_from_config_none_returns_defaults():
    p = RunLimitPolicy.from_config(None)
    assert p.max_runs == 0


def test_runlimit_policy_from_config_values():
    p = RunLimitPolicy.from_config({"max_runs": 3, "window_seconds": 600})
    assert p.max_runs == 3
    assert p.window_seconds == 600


# --- State path ---

def test_get_runlimit_state_path_creates_dir(log_dir):
    path = get_runlimit_state_path(log_dir, "my_job")
    assert os.path.isdir(os.path.join(log_dir, "runlimit"))
    assert path.endswith("my_job.json")


def test_get_runlimit_state_path_sanitises_name(log_dir):
    path = get_runlimit_state_path(log_dir, "my job/name")
    assert " " not in os.path.basename(path)


# --- check_run_limit / record_run ---

def test_check_run_limit_disabled_always_passes(log_dir):
    p = RunLimitPolicy(max_runs=0)
    assert check_run_limit(p, log_dir, "job") is True


def test_check_run_limit_under_limit_passes(log_dir):
    p = RunLimitPolicy(max_runs=3, window_seconds=3600)
    record_run(p, log_dir, "job")
    assert check_run_limit(p, log_dir, "job") is True


def test_check_run_limit_at_limit_fails(log_dir):
    p = RunLimitPolicy(max_runs=2, window_seconds=3600)
    record_run(p, log_dir, "job")
    record_run(p, log_dir, "job")
    assert check_run_limit(p, log_dir, "job") is False


def test_old_timestamps_pruned(log_dir):
    p = RunLimitPolicy(max_runs=2, window_seconds=60)
    path = get_runlimit_state_path(log_dir, "job")
    # Write two timestamps well outside the window
    old = time.time() - 120
    with open(path, "w") as fh:
        json.dump({"timestamps": [old, old]}, fh)
    # Both old entries should be pruned, so the job is allowed
    assert check_run_limit(p, log_dir, "job") is True


def test_record_run_disabled_does_not_write(log_dir):
    p = RunLimitPolicy(max_runs=0)
    record_run(p, log_dir, "job")
    path = get_runlimit_state_path(log_dir, "job")
    assert not os.path.exists(path)
