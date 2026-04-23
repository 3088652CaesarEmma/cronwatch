"""Tests for cronwatch.snapshot_guard."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.snapshot_guard import OutputChangedError, SnapshotGuard
from cronwatch.snapshots import SnapshotPolicy, save_snapshot


@pytest.fixture()
def log_dir(tmp_path: Path):
    with patch("cronwatch.snapshots.get_log_dir", return_value=tmp_path):
        yield tmp_path


def _policy(enabled=True, alert_on_change=True, store_output=False):
    return SnapshotPolicy(enabled=enabled, alert_on_change=alert_on_change, store_output=store_output)


def test_guard_disabled_policy_does_nothing(log_dir: Path):
    guard = SnapshotGuard(_policy(enabled=False), "myjob")
    with guard:
        pass
    changed = guard.check("any output")
    assert changed is False


def test_guard_first_run_saves_snapshot_and_raises(log_dir: Path):
    guard = SnapshotGuard(_policy(), "myjob")
    with guard:
        pass
    with pytest.raises(OutputChangedError) as exc_info:
        guard.check("first output")
    assert exc_info.value.job_name == "myjob"


def test_guard_unchanged_output_does_not_raise(log_dir: Path):
    save_snapshot("myjob", "stable")
    guard = SnapshotGuard(_policy(), "myjob")
    with guard:
        pass
    changed = guard.check("stable")
    assert changed is False


def test_guard_changed_output_raises(log_dir: Path):
    save_snapshot("myjob", "old")
    guard = SnapshotGuard(_policy(), "myjob")
    with guard:
        pass
    with pytest.raises(OutputChangedError):
        guard.check("new")


def test_guard_alert_on_change_false_returns_true_without_raising(log_dir: Path):
    save_snapshot("myjob", "old")
    guard = SnapshotGuard(_policy(alert_on_change=False), "myjob")
    with guard:
        pass
    changed = guard.check("new")
    assert changed is True


def test_guard_does_not_suppress_exceptions(log_dir: Path):
    guard = SnapshotGuard(_policy(), "myjob")
    with pytest.raises(RuntimeError):
        with guard:
            raise RuntimeError("job failed")


def test_output_changed_error_message():
    err = OutputChangedError("backup")
    assert "backup" in str(err)
