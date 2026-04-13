"""Tests for cronwatch.jobs module."""

import pytest
import yaml
from pathlib import Path

from cronwatch.jobs import (
    load_jobs_from_config,
    load_jobs_from_file,
    find_job_by_name,
    filter_jobs_by_tag,
)


SAMPLE_CONFIG = {
    "jobs": [
        {"name": "backup", "command": "/bin/backup.sh", "schedule": "0 2 * * *", "tags": ["infra"]},
        {"name": "report", "command": "/bin/report.sh", "schedule": "0 8 * * 1", "tags": ["reports"]},
        {"name": "cleanup", "command": "/bin/cleanup.sh", "schedule": "30 3 * * *", "enabled": False},
    ]
}


def test_load_jobs_from_config_count():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    assert len(jobs) == 3


def test_load_jobs_names():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    names = [j.name for j in jobs]
    assert "backup" in names
    assert "report" in names


def test_load_jobs_disabled_entry():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    cleanup = next(j for j in jobs if j.name == "cleanup")
    assert cleanup.enabled is False


def test_load_jobs_tags():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    backup = next(j for j in jobs if j.name == "backup")
    assert "infra" in backup.tags


def test_load_jobs_skips_invalid_entries(caplog):
    config = {"jobs": [{"name": "broken"}]}  # missing command and schedule
    jobs = load_jobs_from_config(config)
    assert jobs == []
    assert "Skipping invalid job" in caplog.text


def test_load_jobs_empty_config():
    jobs = load_jobs_from_config({})
    assert jobs == []


def test_load_jobs_from_file(tmp_path):
    config_path = tmp_path / "jobs.yml"
    config_path.write_text(yaml.dump(SAMPLE_CONFIG))
    jobs = load_jobs_from_file(str(config_path))
    assert len(jobs) == 3


def test_find_job_by_name():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    job = find_job_by_name(jobs, "report")
    assert job is not None
    assert job.command == "/bin/report.sh"


def test_find_job_by_name_not_found():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    assert find_job_by_name(jobs, "nonexistent") is None


def test_filter_jobs_by_tag():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    infra_jobs = filter_jobs_by_tag(jobs, "infra")
    assert len(infra_jobs) == 1
    assert infra_jobs[0].name == "backup"


def test_filter_jobs_by_tag_no_match():
    jobs = load_jobs_from_config(SAMPLE_CONFIG)
    assert filter_jobs_by_tag(jobs, "nonexistent-tag") == []
