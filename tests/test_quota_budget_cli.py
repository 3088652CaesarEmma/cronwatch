"""Tests for cronwatch.quota_budget_cli."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.quota_budget_cli import (
    add_quota_budget_subcommands,
    cmd_quota_status,
    cmd_budget_status,
)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"job": "testjob", "config": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_quota_budget_subcommands_registers_quota_status():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_quota_budget_subcommands(sub)
    ns = parser.parse_args(["quota-status", "myjob"])
    assert ns.job == "myjob"


def test_add_quota_budget_subcommands_registers_budget_status():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_quota_budget_subcommands(sub)
    ns = parser.parse_args(["budget-status", "myjob"])
    assert ns.job == "myjob"


# ---------------------------------------------------------------------------
# cmd_quota_status
# ---------------------------------------------------------------------------

def test_cmd_quota_status_disabled_prints_message(capsys):
    disabled_policy = MagicMock(enabled=False)
    with patch("cronwatch.quota_budget_cli.load_config") as mock_cfg, \
         patch("cronwatch.quota_budget_cli.get_log_dir", return_value="/tmp"), \
         patch("cronwatch.quota_budget_cli.QuotaPolicy") as MockQP:
        mock_cfg.return_value = MagicMock(jobs={})
        MockQP.from_config.return_value = disabled_policy
        cmd_quota_status(_make_args())

    out = capsys.readouterr().out
    assert "not enabled" in out


def test_cmd_quota_status_enabled_prints_usage(capsys):
    policy = MagicMock(enabled=True, max_runs=10, window_seconds=3600)
    policy.get_run_count = MagicMock(return_value=3)
    with patch("cronwatch.quota_budget_cli.load_config") as mock_cfg, \
         patch("cronwatch.quota_budget_cli.get_log_dir", return_value="/tmp"), \
         patch("cronwatch.quota_budget_cli.QuotaPolicy") as MockQP:
        mock_cfg.return_value = MagicMock(jobs={})
        MockQP.from_config.return_value = policy
        cmd_quota_status(_make_args(job="backup"))

    out = capsys.readouterr().out
    assert "3" in out
    assert "10" in out
    assert "backup" in out


# ---------------------------------------------------------------------------
# cmd_budget_status
# ---------------------------------------------------------------------------

def test_cmd_budget_status_disabled_prints_message(capsys):
    disabled_policy = MagicMock(enabled=False)
    with patch("cronwatch.quota_budget_cli.load_config") as mock_cfg, \
         patch("cronwatch.quota_budget_cli.get_log_dir", return_value="/tmp"), \
         patch("cronwatch.quota_budget_cli.BudgetPolicy") as MockBP:
        mock_cfg.return_value = MagicMock(jobs={})
        MockBP.from_config.return_value = disabled_policy
        cmd_budget_status(_make_args())

    out = capsys.readouterr().out
    assert "not enabled" in out


def test_cmd_budget_status_enabled_prints_usage(capsys):
    policy = MagicMock(enabled=True, max_seconds=120.0)
    policy.get_used_seconds = MagicMock(return_value=45.0)
    with patch("cronwatch.quota_budget_cli.load_config") as mock_cfg, \
         patch("cronwatch.quota_budget_cli.get_log_dir", return_value="/tmp"), \
         patch("cronwatch.quota_budget_cli.BudgetPolicy") as MockBP:
        mock_cfg.return_value = MagicMock(jobs={})
        MockBP.from_config.return_value = policy
        cmd_budget_status(_make_args(job="report"))

    out = capsys.readouterr().out
    assert "45.0" in out
    assert "120.0" in out
    assert "report" in out


def test_cmd_budget_status_remaining_is_correct(capsys):
    policy = MagicMock(enabled=True, max_seconds=100.0)
    policy.get_used_seconds = MagicMock(return_value=80.0)
    with patch("cronwatch.quota_budget_cli.load_config") as mock_cfg, \
         patch("cronwatch.quota_budget_cli.get_log_dir", return_value="/tmp"), \
         patch("cronwatch.quota_budget_cli.BudgetPolicy") as MockBP:
        mock_cfg.return_value = MagicMock(jobs={})
        MockBP.from_config.return_value = policy
        cmd_budget_status(_make_args(job="report"))

    out = capsys.readouterr().out
    assert "20.0" in out  # remaining
