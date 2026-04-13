"""Tests for cronwatch.log module."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from cronwatch.log import log_result_json, read_job_log, _result_to_dict
from cronwatch.runner import JobResult


@pytest.fixture
def sample_result():
    return JobResult(
        job_name="backup-db",
        command="pg_dump mydb",
        exit_code=0,
        stdout="dump complete",
        stderr="",
        duration=1.23,
        started_at=datetime(2024, 1, 15, 10, 0, 0),
    )


@pytest.fixture
def failed_result():
    return JobResult(
        job_name="backup-db",
        command="pg_dump mydb",
        exit_code=1,
        stdout="",
        stderr="connection refused",
        duration=0.05,
        started_at=datetime(2024, 1, 15, 11, 0, 0),
    )


def test_result_to_dict_success(sample_result):
    d = _result_to_dict(sample_result)
    assert d["job"] == "backup-db"
    assert d["exit_code"] == 0
    assert d["success"] is True
    assert d["duration_seconds"] == 1.23
    assert d["stdout"] == "dump complete"


def test_result_to_dict_failure(failed_result):
    d = _result_to_dict(failed_result)
    assert d["success"] is False
    assert d["stderr"] == "connection refused"


def test_log_result_json_creates_file(tmp_path, sample_result):
    log_file = log_result_json(sample_result, log_dir=tmp_path)
    assert log_file.exists()
    assert log_file.name == "backup-db.log"


def test_log_result_json_valid_json(tmp_path, sample_result):
    log_file = log_result_json(sample_result, log_dir=tmp_path)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["job"] == "backup-db"
    assert "logged_at" in entry


def test_log_result_json_appends(tmp_path, sample_result, failed_result):
    log_result_json(sample_result, log_dir=tmp_path)
    log_result_json(failed_result, log_dir=tmp_path)
    lines = (tmp_path / "backup-db.log").read_text().strip().splitlines()
    assert len(lines) == 2


def test_log_result_sanitizes_job_name(tmp_path):
    result = JobResult(
        job_name="my job/name",
        command="echo hi",
        exit_code=0,
        stdout="hi",
        stderr="",
        duration=0.1,
        started_at=datetime.now(),
    )
    log_file = log_result_json(result, log_dir=tmp_path)
    assert " " not in log_file.name
    assert "/" not in log_file.name


def test_read_job_log_returns_entries(tmp_path, sample_result, failed_result):
    log_result_json(sample_result, log_dir=tmp_path)
    log_result_json(failed_result, log_dir=tmp_path)
    entries = read_job_log("backup-db", log_dir=tmp_path)
    assert len(entries) == 2
    assert entries[0]["exit_code"] == 0
    assert entries[1]["exit_code"] == 1


def test_read_job_log_missing_file(tmp_path):
    entries = read_job_log("nonexistent", log_dir=tmp_path)
    assert entries == []


def test_log_creates_directory(tmp_path, sample_result):
    nested = tmp_path / "deep" / "logs"
    log_result_json(sample_result, log_dir=nested)
    assert nested.is_dir()
