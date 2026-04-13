"""Tests for cronwatch.history module."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.history import append_history, get_history_path, last_run, read_history
from cronwatch.runner import JobResult


@pytest.fixture
def tmp_log_dir(tmp_path):
    return tmp_path


@pytest.fixture
def success_result():
    started = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    finished = datetime(2024, 1, 15, 10, 0, 5, tzinfo=timezone.utc)
    return JobResult(
        job_name="backup",
        command="/usr/bin/backup.sh",
        exit_code=0,
        stdout="done",
        stderr="",
        started_at=started,
        finished_at=finished,
    )


@pytest.fixture
def failed_result():
    started = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
    finished = datetime(2024, 1, 15, 11, 0, 2, tzinfo=timezone.utc)
    return JobResult(
        job_name="backup",
        command="/usr/bin/backup.sh",
        exit_code=1,
        stdout="",
        stderr="error",
        started_at=started,
        finished_at=finished,
    )


def test_get_history_path_uses_log_dir(tmp_log_dir):
    path = get_history_path(tmp_log_dir)
    assert path.parent == tmp_log_dir
    assert path.name == "history.jsonl"


def test_append_history_creates_file(tmp_log_dir, success_result):
    append_history(success_result, log_dir=tmp_log_dir)
    history_file = get_history_path(tmp_log_dir)
    assert history_file.exists()


def test_append_history_writes_valid_json(tmp_log_dir, success_result):
    append_history(success_result, log_dir=tmp_log_dir)
    history_file = get_history_path(tmp_log_dir)
    lines = history_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["job_name"] == "backup"
    assert entry["exit_code"] == 0
    assert entry["success"] is True


def test_append_history_multiple_entries(tmp_log_dir, success_result, failed_result):
    append_history(success_result, log_dir=tmp_log_dir)
    append_history(failed_result, log_dir=tmp_log_dir)
    entries = read_history(log_dir=tmp_log_dir)
    assert len(entries) == 2


def test_read_history_returns_most_recent_first(tmp_log_dir, success_result, failed_result):
    append_history(success_result, log_dir=tmp_log_dir)
    append_history(failed_result, log_dir=tmp_log_dir)
    entries = read_history(log_dir=tmp_log_dir)
    assert entries[0]["exit_code"] == 1
    assert entries[1]["exit_code"] == 0


def test_read_history_filter_by_job_name(tmp_log_dir, success_result):
    other = JobResult(
        job_name="cleanup",
        command="/usr/bin/cleanup.sh",
        exit_code=0,
        stdout="",
        stderr="",
        started_at=success_result.started_at,
        finished_at=success_result.finished_at,
    )
    append_history(success_result, log_dir=tmp_log_dir)
    append_history(other, log_dir=tmp_log_dir)
    entries = read_history(job_name="backup", log_dir=tmp_log_dir)
    assert all(e["job_name"] == "backup" for e in entries)
    assert len(entries) == 1


def test_read_history_empty_when_no_file(tmp_log_dir):
    entries = read_history(log_dir=tmp_log_dir)
    assert entries == []


def test_last_run_returns_most_recent(tmp_log_dir, success_result, failed_result):
    append_history(success_result, log_dir=tmp_log_dir)
    append_history(failed_result, log_dir=tmp_log_dir)
    entry = last_run("backup", log_dir=tmp_log_dir)
    assert entry["exit_code"] == 1


def test_last_run_returns_none_when_no_history(tmp_log_dir):
    assert last_run("nonexistent", log_dir=tmp_log_dir) is None
