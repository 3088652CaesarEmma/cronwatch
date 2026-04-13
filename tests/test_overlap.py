"""Tests for cronwatch.overlap (PID-based overlap detection)."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.overlap import (
    acquire_lock,
    get_lock_dir,
    get_lock_path,
    is_locked,
    release_lock,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def test_get_lock_dir_is_under_log_dir(log_dir: str) -> None:
    assert get_lock_dir(log_dir) == Path(log_dir) / "locks"


def test_get_lock_path_safe_name(log_dir: str) -> None:
    path = get_lock_path(log_dir, "my job/name")
    assert path.name == "my_job_name.pid"


def test_acquire_lock_creates_pid_file(log_dir: str) -> None:
    acquired = acquire_lock(log_dir, "test-job")
    assert acquired is True
    lock_path = get_lock_path(log_dir, "test-job")
    assert lock_path.exists()
    assert int(lock_path.read_text().strip()) == os.getpid()


def test_acquire_lock_returns_false_when_another_process_holds_lock(
    log_dir: str,
) -> None:
    lock_path = get_lock_path(log_dir, "test-job")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # Write a fake PID that appears alive
    lock_path.write_text(str(os.getpid() + 9999))

    with patch("cronwatch.overlap._pid_alive", return_value=True):
        acquired = acquire_lock(log_dir, "test-job")

    assert acquired is False


def test_acquire_lock_removes_stale_lock_and_acquires(log_dir: str) -> None:
    lock_path = get_lock_path(log_dir, "test-job")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("99999")

    with patch("cronwatch.overlap._pid_alive", return_value=False):
        acquired = acquire_lock(log_dir, "test-job")

    assert acquired is True
    assert int(lock_path.read_text().strip()) == os.getpid()


def test_release_lock_removes_file(log_dir: str) -> None:
    acquire_lock(log_dir, "test-job")
    release_lock(log_dir, "test-job")
    assert not get_lock_path(log_dir, "test-job").exists()


def test_release_lock_does_not_remove_foreign_lock(log_dir: str) -> None:
    lock_path = get_lock_path(log_dir, "test-job")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("1")  # PID 1 belongs to init, not us
    release_lock(log_dir, "test-job")
    assert lock_path.exists()


def test_release_lock_is_idempotent(log_dir: str) -> None:
    """Releasing a lock that does not exist should not raise an error."""
    # No lock acquired — calling release should be a no-op
    release_lock(log_dir, "nonexistent-job")
    assert not get_lock_path(log_dir, "nonexistent-job").exists()


def test_is_locked_returns_false_when_no_file(log_dir: str) -> None:
    assert is_locked(log_dir, "ghost-job") is False


def test_is_locked_returns_false_for_own_lock(log_dir: str) -> None:
    acquire_lock(log_dir, "test-job")
    # Current process holds the lock — should not be considered "locked" by another
    assert is_locked(log_dir, "test-job") is False


def test_is_locked_returns_true_when_another_process_holds_lock(
    log_dir: str,
) -> None:
    lock_path = get_lock_path(log_dir, "test-job")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid() + 9999))

    with patch("cronwatch.overlap._pid_alive", return_value=True):
        assert is_locked(log_dir, "test-job") is True
