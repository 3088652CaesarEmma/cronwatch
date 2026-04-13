"""Tests for cronwatch.checkpoint."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from cronwatch.checkpoint import (
    get_checkpoint_path,
    load_checkpoints,
    save_checkpoints,
    record_success,
    last_success,
    seconds_since_success,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def test_get_checkpoint_path_uses_log_dir(log_dir: str) -> None:
    path = get_checkpoint_path(log_dir)
    assert path.parent == Path(log_dir)
    assert path.name == "checkpoints.json"


def test_load_checkpoints_returns_empty_when_no_file(log_dir: str) -> None:
    result = load_checkpoints(log_dir)
    assert result == {}


def test_save_and_load_roundtrip(log_dir: str) -> None:
    data = {"my_job": "2024-01-15T10:30:00+00:00"}
    save_checkpoints(data, log_dir)
    loaded = load_checkpoints(log_dir)
    assert loaded == data


def test_record_success_creates_entry(log_dir: str) -> None:
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    record_success("backup", log_dir, ts=ts)
    checkpoints = load_checkpoints(log_dir)
    assert "backup" in checkpoints


def test_record_success_overwrites_previous(log_dir: str) -> None:
    ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ts2 = datetime(2024, 6, 1, tzinfo=timezone.utc)
    record_success("backup", log_dir, ts=ts1)
    record_success("backup", log_dir, ts=ts2)
    checkpoints = load_checkpoints(log_dir)
    assert checkpoints["backup"] == ts2.isoformat()


def test_last_success_returns_none_when_never_run(log_dir: str) -> None:
    result = last_success("nonexistent_job", log_dir)
    assert result is None


def test_last_success_returns_datetime(log_dir: str) -> None:
    ts = datetime(2024, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    record_success("cleanup", log_dir, ts=ts)
    result = last_success("cleanup", log_dir)
    assert result is not None
    assert result.year == 2024
    assert result.month == 3
    assert result.day == 10


def test_seconds_since_success_returns_none_when_never_run(log_dir: str) -> None:
    assert seconds_since_success("ghost_job", log_dir) is None


def test_seconds_since_success_returns_positive_float(log_dir: str) -> None:
    past = datetime.now(timezone.utc) - timedelta(seconds=120)
    record_success("report", log_dir, ts=past)
    elapsed = seconds_since_success("report", log_dir)
    assert elapsed is not None
    assert elapsed >= 100  # allow some slack


def test_multiple_jobs_stored_independently(log_dir: str) -> None:
    ts_a = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ts_b = datetime(2024, 6, 1, tzinfo=timezone.utc)
    record_success("job_a", log_dir, ts=ts_a)
    record_success("job_b", log_dir, ts=ts_b)
    assert last_success("job_a", log_dir) != last_success("job_b", log_dir)


def test_load_checkpoints_handles_corrupt_file(log_dir: str) -> None:
    path = get_checkpoint_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json")
    result = load_checkpoints(log_dir)
    assert result == {}
