"""Tests for cronwatch.budget."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.budget import (
    BudgetPolicy,
    budget_used,
    check_budget,
    get_budget_state_path,
    record_run,
)


@pytest.fixture()
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("CRONWATCH_LOG_DIR", str(tmp_path))
    return tmp_path


# --- BudgetPolicy ---

def test_budget_policy_defaults():
    p = BudgetPolicy()
    assert p.max_seconds == 0.0
    assert p.window_seconds == 3600.0
    assert not p.enabled


def test_budget_policy_enabled_when_nonzero():
    p = BudgetPolicy(max_seconds=300.0)
    assert p.enabled


def test_budget_policy_negative_max_raises():
    with pytest.raises(ValueError, match="max_seconds"):
        BudgetPolicy(max_seconds=-1.0)


def test_budget_policy_zero_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        BudgetPolicy(max_seconds=60.0, window_seconds=0.0)


def test_budget_policy_from_config_none_returns_defaults():
    p = BudgetPolicy.from_config(None)
    assert p.max_seconds == 0.0


def test_budget_policy_from_config_values():
    p = BudgetPolicy.from_config({"max_seconds": 120, "window_seconds": 1800})
    assert p.max_seconds == 120.0
    assert p.window_seconds == 1800.0


# --- State path ---

def test_get_budget_state_path_uses_log_dir(log_dir):
    path = get_budget_state_path("myjob")
    assert str(log_dir) in str(path)
    assert "myjob" in path.name


# --- record_run / budget_used ---

def test_record_run_creates_file(log_dir):
    record_run("job1", 10.0)
    path = get_budget_state_path("job1")
    assert path.exists()


def test_budget_used_sums_durations(log_dir):
    policy = BudgetPolicy(max_seconds=600.0, window_seconds=3600.0)
    record_run("job2", 30.0)
    record_run("job2", 45.0)
    used = budget_used("job2", policy)
    assert used == pytest.approx(75.0)


def test_budget_used_ignores_old_runs(log_dir):
    policy = BudgetPolicy(max_seconds=600.0, window_seconds=60.0)
    path = get_budget_state_path("job3")
    path.parent.mkdir(parents=True, exist_ok=True)
    old_ts = time.time() - 120  # outside window
    path.write_text(json.dumps({"runs": [{"ts": old_ts, "duration": 500.0}]}))
    used = budget_used("job3", policy)
    assert used == pytest.approx(0.0)


# --- check_budget ---

def test_check_budget_disabled_always_passes(log_dir):
    policy = BudgetPolicy(max_seconds=0.0)
    assert check_budget("any_job", policy) is True


def test_check_budget_under_limit_returns_true(log_dir):
    policy = BudgetPolicy(max_seconds=300.0, window_seconds=3600.0)
    record_run("job4", 50.0)
    assert check_budget("job4", policy) is True


def test_check_budget_over_limit_returns_false(log_dir):
    policy = BudgetPolicy(max_seconds=100.0, window_seconds=3600.0)
    record_run("job5", 60.0)
    record_run("job5", 60.0)
    assert check_budget("job5", policy) is False
