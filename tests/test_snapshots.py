"""Tests for cronwatch.snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.snapshots import (
    SnapshotPolicy,
    _hash_output,
    get_snapshot_path,
    load_snapshot,
    output_changed,
    save_snapshot,
)


@pytest.fixture()
def log_dir(tmp_path: Path):
    with patch("cronwatch.snapshots.get_log_dir", return_value=tmp_path):
        yield tmp_path


def test_snapshot_policy_defaults():
    p = SnapshotPolicy()
    assert p.enabled is False
    assert p.alert_on_change is True
    assert p.store_output is False


def test_snapshot_policy_from_config_none_returns_defaults():
    p = SnapshotPolicy.from_config(None)
    assert p.enabled is False


def test_snapshot_policy_from_config_sets_fields():
    p = SnapshotPolicy.from_config({"enabled": True, "store_output": True, "alert_on_change": False})
    assert p.enabled is True
    assert p.store_output is True
    assert p.alert_on_change is False


def test_snapshot_policy_invalid_alert_on_change_raises():
    with pytest.raises(TypeError):
        SnapshotPolicy(alert_on_change="yes")  # type: ignore


def test_hash_output_is_deterministic():
    assert _hash_output("hello") == _hash_output("hello")


def test_hash_output_differs_for_different_input():
    assert _hash_output("hello") != _hash_output("world")


def test_get_snapshot_path_uses_log_dir(log_dir: Path):
    path = get_snapshot_path("myjob")
    assert path == log_dir / "snapshots" / "myjob.json"


def test_save_snapshot_creates_file(log_dir: Path):
    save_snapshot("myjob", "some output")
    path = log_dir / "snapshots" / "myjob.json"
    assert path.exists()


def test_save_and_load_roundtrip(log_dir: Path):
    save_snapshot("myjob", "hello world")
    data = load_snapshot("myjob")
    assert data is not None
    assert data["output"] == "hello world"
    assert data["hash"] == _hash_output("hello world")


def test_load_snapshot_returns_none_when_missing(log_dir: Path):
    assert load_snapshot("nonexistent") is None


def test_output_changed_true_when_no_snapshot(log_dir: Path):
    assert output_changed("myjob", "anything") is True


def test_output_changed_false_when_same(log_dir: Path):
    save_snapshot("myjob", "stable output")
    assert output_changed("myjob", "stable output") is False


def test_output_changed_true_when_different(log_dir: Path):
    save_snapshot("myjob", "old output")
    assert output_changed("myjob", "new output") is True
