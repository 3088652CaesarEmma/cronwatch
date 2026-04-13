"""Tests for cronwatch.filter module."""

import pytest

from cronwatch.scheduler import CronEntry
from cronwatch.filter import (
    filter_by_name,
    filter_by_tag,
    filter_by_tags_any,
    filter_by_tags_all,
    filter_enabled,
    filter_disabled,
    search_jobs,
)


@pytest.fixture
def jobs():
    return [
        CronEntry(name="backup", command="/usr/bin/backup.sh", schedule="0 2 * * *", tags=["infra", "nightly"], disabled=False),
        CronEntry(name="cleanup", command="/usr/bin/cleanup.sh", schedule="0 3 * * *", tags=["infra"], disabled=False),
        CronEntry(name="report", command="/usr/bin/report.py", schedule="0 6 * * 1", tags=["reporting", "nightly"], disabled=False),
        CronEntry(name="old-job", command="/usr/bin/old.sh", schedule="* * * * *", tags=[], disabled=True),
    ]


def test_filter_by_name_found(jobs):
    result = filter_by_name(jobs, "backup")
    assert result is not None
    assert result.name == "backup"


def test_filter_by_name_not_found(jobs):
    result = filter_by_name(jobs, "nonexistent")
    assert result is None


def test_filter_by_tag_single(jobs):
    result = filter_by_tag(jobs, "reporting")
    assert len(result) == 1
    assert result[0].name == "report"


def test_filter_by_tag_multiple(jobs):
    result = filter_by_tag(jobs, "infra")
    assert len(result) == 2
    names = {j.name for j in result}
    assert names == {"backup", "cleanup"}


def test_filter_by_tags_any(jobs):
    result = filter_by_tags_any(jobs, ["reporting", "nightly"])
    names = {j.name for j in result}
    assert names == {"backup", "report"}


def test_filter_by_tags_all(jobs):
    result = filter_by_tags_all(jobs, ["infra", "nightly"])
    assert len(result) == 1
    assert result[0].name == "backup"


def test_filter_by_tags_all_no_match(jobs):
    result = filter_by_tags_all(jobs, ["infra", "reporting"])
    assert result == []


def test_filter_enabled(jobs):
    result = filter_enabled(jobs)
    assert len(result) == 3
    assert all(not getattr(j, 'disabled', False) for j in result)


def test_filter_disabled(jobs):
    result = filter_disabled(jobs)
    assert len(result) == 1
    assert result[0].name == "old-job"


def test_search_jobs_by_name(jobs):
    result = search_jobs(jobs, "back")
    assert len(result) == 1
    assert result[0].name == "backup"


def test_search_jobs_by_command(jobs):
    result = search_jobs(jobs, ".py")
    assert len(result) == 1
    assert result[0].name == "report"


def test_search_jobs_case_insensitive(jobs):
    result = search_jobs(jobs, "BACKUP")
    assert len(result) == 1


def test_search_jobs_no_match(jobs):
    result = search_jobs(jobs, "zzznomatch")
    assert result == []
