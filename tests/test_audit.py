"""Tests for cronwatch.audit."""
import json
from pathlib import Path

import pytest

from cronwatch.audit import (
    AuditEntry,
    get_audit_path,
    record_audit,
    read_audit,
)
from cronwatch.runner import JobResult


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def success_result():
    return JobResult(command="echo hello", exit_code=0, stdout="hello\n", stderr="")


@pytest.fixture
def failed_result():
    return JobResult(command="false", exit_code=1, stdout="", stderr="error")


def test_get_audit_path_uses_log_dir(log_dir):
    path = get_audit_path(log_dir)
    assert path.parent == Path(log_dir)
    assert path.name == "audit.jsonl"


def test_record_audit_creates_file(log_dir, success_result):
    record_audit(success_result, log_dir, job_name="test-job")
    assert get_audit_path(log_dir).exists()


def test_record_audit_returns_entry(log_dir, success_result):
    entry = record_audit(success_result, log_dir, job_name="test-job")
    assert isinstance(entry, AuditEntry)
    assert entry.job_name == "test-job"
    assert entry.exit_code == 0


def test_record_audit_appends_jsonl(log_dir, success_result, failed_result):
    record_audit(success_result, log_dir, job_name="job-a")
    record_audit(failed_result, log_dir, job_name="job-b")
    lines = get_audit_path(log_dir).read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["job_name"] == "job-a"
    assert json.loads(lines[1])["job_name"] == "job-b"


def test_record_audit_stores_triggered_by(log_dir, success_result):
    entry = record_audit(success_result, log_dir, triggered_by="scheduler")
    assert entry.triggered_by == "scheduler"


def test_record_audit_stores_tags(log_dir, success_result):
    entry = record_audit(success_result, log_dir, tags=["nightly", "db"])
    assert "nightly" in entry.tags
    assert "db" in entry.tags


def test_record_audit_stores_note(log_dir, success_result):
    entry = record_audit(success_result, log_dir, note="manual trigger by admin")
    assert entry.note == "manual trigger by admin"


def test_read_audit_returns_empty_when_no_file(log_dir):
    assert read_audit(log_dir) == []


def test_read_audit_returns_entries(log_dir, success_result, failed_result):
    record_audit(success_result, log_dir, job_name="alpha")
    record_audit(failed_result, log_dir, job_name="beta")
    entries = read_audit(log_dir)
    assert len(entries) == 2
    assert entries[0].job_name == "alpha"
    assert entries[1].job_name == "beta"


def test_read_audit_respects_limit(log_dir, success_result):
    for i in range(10):
        record_audit(success_result, log_dir, job_name=f"job-{i}")
    entries = read_audit(log_dir, limit=3)
    assert len(entries) == 3
    assert entries[-1].job_name == "job-9"


def test_read_audit_skips_corrupt_lines(log_dir, success_result):
    record_audit(success_result, log_dir, job_name="good")
    with get_audit_path(log_dir).open("a") as fh:
        fh.write("{corrupt\n")
    entries = read_audit(log_dir)
    assert len(entries) == 1
    assert entries[0].job_name == "good"


def test_audit_entry_default_tags_are_list():
    entry = AuditEntry(
        job_name="x", command="echo", started_at="t", finished_at="t",
        exit_code=0, duration_seconds=0.1
    )
    assert entry.tags == []
