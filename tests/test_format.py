"""Tests for cronwatch.format module."""

import pytest

from cronwatch.scheduler import CronEntry
from cronwatch.format import format_job_table, format_job_names, format_job_count


@pytest.fixture
def jobs():
    return [
        CronEntry(name="backup", command="/usr/bin/backup.sh", schedule="0 2 * * *", tags=["infra"], disabled=False),
        CronEntry(name="report", command="/usr/bin/report.py", schedule="0 6 * * 1", tags=["reporting"], disabled=False),
        CronEntry(name="old-job", command="/usr/bin/old.sh", schedule="* * * * *", tags=[], disabled=True),
    ]


def test_format_job_table_contains_headers(jobs):
    output = format_job_table(jobs)
    assert "NAME" in output
    assert "SCHEDULE" in output
    assert "COMMAND" in output
    assert "STATUS" in output


def test_format_job_table_contains_job_names(jobs):
    output = format_job_table(jobs)
    assert "backup" in output
    assert "report" in output
    assert "old-job" in output


def test_format_job_table_shows_disabled_status(jobs):
    output = format_job_table(jobs)
    assert "[disabled]" in output


def test_format_job_table_shows_enabled_status(jobs):
    output = format_job_table(jobs)
    assert "enabled" in output


def test_format_job_table_shows_tags(jobs):
    output = format_job_table(jobs)
    assert "infra" in output
    assert "reporting" in output


def test_format_job_table_empty_list():
    output = format_job_table([])
    assert output == "No jobs found."


def test_format_job_table_truncates_long_command():
    long_cmd = "/usr/bin/" + "a" * 80
    job = CronEntry(name="long", command=long_cmd, schedule="* * * * *", tags=[], disabled=False)
    output = format_job_table([job], max_cmd_width=20)
    assert "..." in output


def test_format_job_names_lists_all(jobs):
    output = format_job_names(jobs)
    lines = output.splitlines()
    assert len(lines) == 3
    assert "backup" in lines
    assert "report" in lines


def test_format_job_names_empty():
    output = format_job_names([])
    assert output == "No jobs found."


def test_format_job_count_totals(jobs):
    output = format_job_count(jobs)
    assert "Total: 3" in output
    assert "Enabled: 2" in output
    assert "Disabled: 1" in output


def test_format_job_count_all_enabled():
    jobs = [
        CronEntry(name="a", command="cmd", schedule="* * * * *", tags=[], disabled=False),
        CronEntry(name="b", command="cmd", schedule="* * * * *", tags=[], disabled=False),
    ]
    output = format_job_count(jobs)
    assert "Total: 2" in output
    assert "Disabled: 0" in output
