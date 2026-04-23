"""Tests for cronwatch.roster and cronwatch.roster_guard."""
import json
import os
import pytest

from cronwatch.roster import (
    RosterEntry,
    get_roster_path,
    load_roster,
    save_roster,
    register_job,
    deregister_job,
    list_roster,
)
from cronwatch.roster_guard import JobNotRegisteredError, RosterGuard


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# get_roster_path
# ---------------------------------------------------------------------------

def test_get_roster_path_uses_log_dir(log_dir):
    path = get_roster_path(log_dir)
    assert path.startswith(log_dir)
    assert path.endswith("roster.json")


# ---------------------------------------------------------------------------
# load / save round-trip
# ---------------------------------------------------------------------------

def test_load_roster_returns_empty_when_no_file(log_dir):
    assert load_roster(log_dir) == {}


def test_save_and_load_roundtrip(log_dir):
    entry = RosterEntry(name="backup", command="/usr/bin/backup", tags=["db"])
    save_roster({"backup": entry}, log_dir)
    roster = load_roster(log_dir)
    assert "backup" in roster
    assert roster["backup"].command == "/usr/bin/backup"
    assert roster["backup"].tags == ["db"]


# ---------------------------------------------------------------------------
# register_job
# ---------------------------------------------------------------------------

def test_register_job_creates_entry(log_dir):
    entry = register_job("sync", "rsync -a /src /dst", log_dir=log_dir)
    assert entry.name == "sync"
    assert entry.command == "rsync -a /src /dst"


def test_register_job_persists_to_disk(log_dir):
    register_job("sync", "rsync -a /src /dst", log_dir=log_dir)
    roster = load_roster(log_dir)
    assert "sync" in roster


def test_register_job_updates_existing_entry(log_dir):
    register_job("sync", "rsync -a /src /dst", log_dir=log_dir)
    register_job("sync", "rsync -avz /src /dst", tags=["network"], log_dir=log_dir)
    roster = load_roster(log_dir)
    assert roster["sync"].command == "rsync -avz /src /dst"
    assert roster["sync"].tags == ["network"]


# ---------------------------------------------------------------------------
# deregister_job
# ---------------------------------------------------------------------------

def test_deregister_job_removes_entry(log_dir):
    register_job("cleanup", "rm -rf /tmp/old", log_dir=log_dir)
    result = deregister_job("cleanup", log_dir=log_dir)
    assert result is True
    assert "cleanup" not in load_roster(log_dir)


def test_deregister_job_returns_false_when_not_found(log_dir):
    assert deregister_job("nonexistent", log_dir=log_dir) is False


# ---------------------------------------------------------------------------
# list_roster
# ---------------------------------------------------------------------------

def test_list_roster_sorted_by_name(log_dir):
    register_job("zebra", "z", log_dir=log_dir)
    register_job("alpha", "a", log_dir=log_dir)
    names = [e.name for e in list_roster(log_dir)]
    assert names == ["alpha", "zebra"]


# ---------------------------------------------------------------------------
# RosterGuard
# ---------------------------------------------------------------------------

def test_guard_allows_registered_job(log_dir):
    register_job("myjob", "echo hi", log_dir=log_dir)
    with RosterGuard("myjob", "echo hi", log_dir=log_dir):
        pass  # should not raise


def test_guard_raises_for_unregistered_job(log_dir):
    with pytest.raises(JobNotRegisteredError) as exc_info:
        with RosterGuard("ghost", "echo boo", log_dir=log_dir):
            pass
    assert "ghost" in str(exc_info.value)


def test_guard_auto_register_creates_entry(log_dir):
    with RosterGuard("newjob", "echo new", auto_register=True, log_dir=log_dir):
        pass
    assert "newjob" in load_roster(log_dir)


def test_guard_does_not_suppress_exceptions(log_dir):
    register_job("errjob", "echo err", log_dir=log_dir)
    with pytest.raises(RuntimeError):
        with RosterGuard("errjob", "echo err", log_dir=log_dir):
            raise RuntimeError("boom")


def test_error_message_contains_job_name():
    err = JobNotRegisteredError("my_special_job")
    assert "my_special_job" in str(err)
