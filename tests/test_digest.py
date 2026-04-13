"""Tests for cronwatch.digest module."""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.digest import (
    DigestPolicy,
    build_digest,
    get_digest_state_path,
    is_digest_due,
    load_digest_state,
    mark_digest_sent,
    save_digest_state,
)


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def success_result():
    r = MagicMock()
    r.exit_code = 0
    r.command = "echo ok"
    return r


@pytest.fixture
def failed_result():
    r = MagicMock()
    r.exit_code = 1
    r.command = "false"
    return r


def test_digest_policy_defaults():
    p = DigestPolicy()
    assert p.enabled is False
    assert p.interval_hours == 24
    assert p.only_on_failure is False


def test_digest_policy_invalid_interval():
    with pytest.raises(ValueError):
        DigestPolicy(interval_hours=0)


def test_digest_policy_from_config():
    cfg = {"digest": {"enabled": True, "interval_hours": 6, "only_on_failure": True}}
    p = DigestPolicy.from_config(cfg)
    assert p.enabled is True
    assert p.interval_hours == 6
    assert p.only_on_failure is True


def test_get_digest_state_path(log_dir):
    path = get_digest_state_path(log_dir)
    assert path.endswith("digest_state.json")
    assert log_dir in path


def test_load_digest_state_missing_file(log_dir):
    assert load_digest_state(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    state = {"last_sent": "2024-01-01T00:00:00"}
    save_digest_state(log_dir, state)
    loaded = load_digest_state(log_dir)
    assert loaded == state


def test_is_digest_due_no_state(log_dir):
    policy = DigestPolicy(enabled=True, interval_hours=24)
    assert is_digest_due(policy, log_dir) is True


def test_is_digest_due_recently_sent(log_dir):
    policy = DigestPolicy(enabled=True, interval_hours=24)
    state = {"last_sent": datetime.utcnow().isoformat()}
    save_digest_state(log_dir, state)
    assert is_digest_due(policy, log_dir) is False


def test_is_digest_due_old_state(log_dir):
    policy = DigestPolicy(enabled=True, interval_hours=1)
    old = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    save_digest_state(log_dir, {"last_sent": old})
    assert is_digest_due(policy, log_dir) is True


def test_is_digest_due_disabled(log_dir):
    policy = DigestPolicy(enabled=False)
    assert is_digest_due(policy, log_dir) is False


def test_mark_digest_sent(log_dir):
    mark_digest_sent(log_dir)
    state = load_digest_state(log_dir)
    assert "last_sent" in state
