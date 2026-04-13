"""Tests for cronwatch.summary module."""

import pytest

from cronwatch.runner import JobResult
from cronwatch.summary import RunSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def success_result():
    return JobResult(command="echo ok", exit_code=0, stdout="ok\n", stderr="")


@pytest.fixture()
def failed_result():
    return JobResult(command="false", exit_code=1, stdout="", stderr="error\n")


@pytest.fixture()
def mixed_summary(success_result, failed_result):
    s = RunSummary()
    s.add(success_result)
    s.add(failed_result)
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_empty_summary_totals():
    s = RunSummary()
    assert s.total == 0
    assert s.success_count == 0
    assert s.failure_count == 0
    assert s.all_passed is False


def test_add_results(success_result, failed_result):
    s = RunSummary()
    s.add(success_result)
    s.add(failed_result)
    assert s.total == 2


def test_success_count(mixed_summary):
    assert mixed_summary.success_count == 1


def test_failure_count(mixed_summary):
    assert mixed_summary.failure_count == 1


def test_all_passed_when_no_failures(success_result):
    s = RunSummary(results=[success_result])
    assert s.all_passed is True


def test_all_passed_false_when_failures(mixed_summary):
    assert mixed_summary.all_passed is False


def test_as_text_contains_totals(mixed_summary):
    text = mixed_summary.as_text()
    assert "Total jobs" in text
    assert "2" in text


def test_as_text_lists_failed_commands(mixed_summary):
    text = mixed_summary.as_text()
    assert "false" in text


def test_as_text_no_failed_section_when_all_pass(success_result):
    s = RunSummary(results=[success_result])
    text = s.as_text()
    assert "Failed jobs" not in text


def test_as_dict_keys(mixed_summary):
    d = mixed_summary.as_dict()
    assert set(d.keys()) == {"total", "succeeded", "failed", "all_passed", "failed_jobs"}


def test_as_dict_failed_jobs_list(mixed_summary):
    d = mixed_summary.as_dict()
    assert len(d["failed_jobs"]) == 1
    assert d["failed_jobs"][0]["command"] == "false"
    assert d["failed_jobs"][0]["exit_code"] == 1
