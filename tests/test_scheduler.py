"""Tests for cronwatch.scheduler module."""

import pytest
from datetime import datetime

from cronwatch.scheduler import (
    CronEntry,
    parse_cron_field,
    is_due,
    get_due_jobs,
)


# --- CronEntry ---

def test_cron_entry_creation():
    entry = CronEntry(name="backup", command="/usr/bin/backup.sh", schedule="0 2 * * *")
    assert entry.name == "backup"
    assert entry.enabled is True
    assert entry.tags == []


def test_cron_entry_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        CronEntry(name="", command="echo hi", schedule="* * * * *")


def test_cron_entry_empty_command_raises():
    with pytest.raises(ValueError, match="command"):
        CronEntry(name="job", command="", schedule="* * * * *")


# --- parse_cron_field ---

def test_parse_wildcard():
    assert parse_cron_field("*", 0, 4) == [0, 1, 2, 3, 4]


def test_parse_single_value():
    assert parse_cron_field("3", 0, 59) == [3]


def test_parse_range():
    assert parse_cron_field("1-3", 0, 59) == [1, 2, 3]


def test_parse_step():
    assert parse_cron_field("*/15", 0, 59) == [0, 15, 30, 45]


def test_parse_list():
    assert parse_cron_field("1,3,5", 0, 59) == [1, 3, 5]


# --- is_due ---

def test_is_due_every_minute():
    dt = datetime(2024, 6, 1, 10, 25)
    assert is_due("* * * * *", dt) is True


def test_is_due_specific_time_match():
    dt = datetime(2024, 6, 1, 2, 0)
    assert is_due("0 2 * * *", dt) is True


def test_is_due_specific_time_no_match():
    dt = datetime(2024, 6, 1, 3, 0)
    assert is_due("0 2 * * *", dt) is False


def test_is_due_invalid_schedule_raises():
    with pytest.raises(ValueError):
        is_due("* * * *", datetime.now())


# --- get_due_jobs ---

def test_get_due_jobs_returns_matching():
    dt = datetime(2024, 6, 1, 0, 0)
    jobs = [
        CronEntry(name="midnight", command="echo midnight", schedule="0 0 * * *"),
        CronEntry(name="noon", command="echo noon", schedule="0 12 * * *"),
    ]
    due = get_due_jobs(jobs, dt)
    assert len(due) == 1
    assert due[0].name == "midnight"


def test_get_due_jobs_skips_disabled():
    dt = datetime(2024, 6, 1, 0, 0)
    jobs = [
        CronEntry(name="disabled", command="echo hi", schedule="0 0 * * *", enabled=False),
    ]
    assert get_due_jobs(jobs, dt) == []


def test_get_due_jobs_skips_invalid_schedule(caplog):
    dt = datetime(2024, 6, 1, 0, 0)
    jobs = [
        CronEntry(name="bad", command="echo bad", schedule="bad schedule"),
    ]
    due = get_due_jobs(jobs, dt)
    assert due == []
    assert "Skipping job" in caplog.text
