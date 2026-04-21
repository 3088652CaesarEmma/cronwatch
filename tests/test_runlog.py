"""Tests for cronwatch/runlog.py"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.runner import JobResult
from cronwatch.runlog import (
    RunLogEntry,
    append_run_log,
    get_runlog_path,
    last_run_entry,
    read_run_log,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def success_result() -> JobResult:
    return JobResult(
        command="echo hello",
        exit_code=0,
        stdout="hello\n",
        stderr="",
        duration=0.12,
    )


@pytest.fixture()
def failed_result() -> JobResult:
    return JobResult(
        command="false",
        exit_code=1,
        stdout="",
        stderr="error occurred\n",
        duration=0.05,
    )


def test_get_runlog_path_uses_log_dir(log_dir: Path) -> None:
    path = get_runlog_path(str(log_dir))
    assert path.parent == log_dir
    assert path.name == "runlog.jsonl"


def test_append_run_log_creates_file(log_dir: Path, success_result: JobResult) -> None:
    append_run_log(success_result, "backup", log_dir=str(log_dir))
    assert get_runlog_path(str(log_dir)).exists()


def test_append_run_log_returns_entry(log_dir: Path, success_result: JobResult) -> None:
    entry = append_run_log(success_result, "backup", log_dir=str(log_dir))
    assert isinstance(entry, RunLogEntry)
    assert entry.job_name == "backup"
    assert entry.command == "echo hello"
    assert entry.exit_code == 0
    assert entry.success is True


def test_append_run_log_records_failure(log_dir: Path, failed_result: JobResult) -> None:
    entry = append_run_log(failed_result, "cleanup", log_dir=str(log_dir))
    assert entry.exit_code == 1
    assert entry.success is False
    assert entry.stderr_lines == 1


def test_append_run_log_records_stdout_lines(log_dir: Path, success_result: JobResult) -> None:
    entry = append_run_log(success_result, "backup", log_dir=str(log_dir))
    assert entry.stdout_lines == 1


def test_append_run_log_with_note(log_dir: Path, success_result: JobResult) -> None:
    entry = append_run_log(success_result, "backup", log_dir=str(log_dir), note="retried")
    assert entry.note == "retried"


def test_read_run_log_returns_empty_when_no_file(log_dir: Path) -> None:
    entries = read_run_log(log_dir=str(log_dir))
    assert entries == []


def test_read_run_log_returns_all_entries(log_dir: Path, success_result: JobResult, failed_result: JobResult) -> None:
    append_run_log(success_result, "job-a", log_dir=str(log_dir))
    append_run_log(failed_result, "job-b", log_dir=str(log_dir))
    entries = read_run_log(log_dir=str(log_dir))
    assert len(entries) == 2
    assert entries[0].job_name == "job-a"
    assert entries[1].job_name == "job-b"


def test_runlog_file_is_valid_jsonl(log_dir: Path, success_result: JobResult) -> None:
    append_run_log(success_result, "backup", log_dir=str(log_dir))
    path = get_runlog_path(str(log_dir))
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert "timestamp" in data
    assert data["command"] == "echo hello"


def test_last_run_entry_returns_most_recent(log_dir: Path, success_result: JobResult, failed_result: JobResult) -> None:
    append_run_log(success_result, "backup", log_dir=str(log_dir))
    append_run_log(failed_result, "backup", log_dir=str(log_dir))
    entry = last_run_entry("backup", log_dir=str(log_dir))
    assert entry is not None
    assert entry.exit_code == 1


def test_last_run_entry_returns_none_when_no_match(log_dir: Path, success_result: JobResult) -> None:
    append_run_log(success_result, "other-job", log_dir=str(log_dir))
    entry = last_run_entry("backup", log_dir=str(log_dir))
    assert entry is None


def test_runlog_entry_empty_job_name_raises() -> None:
    with pytest.raises(ValueError, match="job_name"):
        RunLogEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            job_name="",
            command="echo",
            exit_code=0,
            duration=0.1,
            success=True,
            stdout_lines=0,
            stderr_lines=0,
        )


def test_runlog_entry_negative_duration_raises() -> None:
    with pytest.raises(ValueError, match="duration"):
        RunLogEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            job_name="backup",
            command="echo",
            exit_code=0,
            duration=-1.0,
            success=True,
            stdout_lines=0,
            stderr_lines=0,
        )
