"""Tests for the cronwatch CLI module."""

import pytest
from unittest.mock import patch, MagicMock

from cronwatch.cli import build_parser, main, cmd_list, cmd_run
from cronwatch.runner import JobResult


@pytest.fixture
def mock_config(tmp_path):
    cfg = tmp_path / "cronwatch.yml"
    cfg.write_text(
        "jobs:\n"
        "  - name: hello\n"
        "    command: echo hello\n"
        "    schedule: '* * * * *'\n"
        "    tags: [test]\n"
        "  - name: world\n"
        "    command: echo world\n"
        "    schedule: '0 * * * *'\n"
        "    enabled: false\n"
    )
    return str(cfg)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser.prog == "cronwatch"


def test_parser_run_subcommand():
    parser = build_parser()
    args = parser.parse_args(["run", "myjob"])
    assert args.command == "run"
    assert args.job_name == "myjob"


def test_parser_run_due_subcommand():
    parser = build_parser()
    args = parser.parse_args(["run-due"])
    assert args.command == "run-due"


def test_parser_list_subcommand():
    parser = build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_parser_list_with_tag():
    parser = build_parser()
    args = parser.parse_args(["list", "--tag", "prod"])
    assert args.tag == "prod"


def test_parser_custom_config():
    parser = build_parser()
    args = parser.parse_args(["-c", "custom.yml", "list"])
    assert args.config == "custom.yml"


def test_cmd_list_all_jobs(mock_config, capsys):
    result = cmd_list(mock_config, tag=None)
    assert result == 0
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" in captured.out


def test_cmd_list_filtered_by_tag(mock_config, capsys):
    result = cmd_list(mock_config, tag="test")
    assert result == 0
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" not in captured.out


def test_cmd_run_unknown_job(mock_config, capsys):
    result = cmd_run("nonexistent", mock_config)
    assert result == 2


def test_cmd_run_known_job(mock_config):
    with patch("cronwatch.cli.notify") as mock_notify:
        result = cmd_run("hello", mock_config)
    assert result == 0
    mock_notify.assert_called_once()


def test_main_no_subcommand_exits_zero():
    result = main([])
    assert result == 0


def test_main_run_due_no_jobs_due(mock_config, capsys):
    with patch("cronwatch.cli.get_due_jobs", return_value=[]):
        result = main(["-c", mock_config, "run-due"])
    assert result == 0
    captured = capsys.readouterr()
    assert "No jobs" in captured.out
