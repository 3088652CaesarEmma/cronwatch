"""Tests for the cronwatch runner module."""

import pytest
from unittest.mock import patch
import subprocess

from cronwatch.runner import run_job, JobResult


def test_successful_command_returns_exit_code_zero():
    result = run_job("echo hello")
    assert result.exit_code == 0
    assert result.success is True


def test_failed_command_returns_nonzero_exit_code():
    result = run_job("exit 1", shell=True)
    assert result.exit_code != 0
    assert result.success is False


def test_stdout_is_captured():
    result = run_job("echo 'hello world'")
    assert "hello world" in result.stdout


def test_stderr_is_captured():
    result = run_job("echo 'error message' >&2", shell=True)
    assert "error message" in result.stderr


def test_command_stored_in_result():
    cmd = "echo test"
    result = run_job(cmd)
    assert result.command == cmd


def test_duration_is_positive():
    result = run_job("echo hello")
    assert result.duration_seconds >= 0.0


def test_started_and_finished_at_are_set():
    result = run_job("echo hello")
    assert result.started_at is not None
    assert result.finished_at is not None
    assert result.finished_at >= result.started_at


def test_timeout_sets_exit_code_negative_one():
    result = run_job("sleep 10", timeout=1)
    assert result.exit_code == -1
    assert result.success is False
    assert "timed out" in result.stderr.lower()


def test_summary_contains_success_status():
    result = run_job("echo hello")
    assert "SUCCESS" in result.summary()


def test_summary_contains_failure_status():
    result = run_job("exit 2", shell=True)
    assert "FAILURE" in result.summary()


def test_summary_contains_command():
    cmd = "echo summary_test"
    result = run_job(cmd)
    assert cmd in result.summary()
