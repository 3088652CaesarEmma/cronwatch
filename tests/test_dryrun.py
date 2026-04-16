"""Tests for cronwatch.dryrun."""
import pytest

from cronwatch.dryrun import DryRunPolicy, DryRunRecorder, make_dry_run_result


# ---------------------------------------------------------------------------
# DryRunPolicy
# ---------------------------------------------------------------------------

def test_dryrun_policy_defaults():
    policy = DryRunPolicy()
    assert policy.enabled is False


def test_dryrun_policy_enabled():
    policy = DryRunPolicy(enabled=True)
    assert policy.enabled is True


def test_dryrun_policy_invalid_type_raises():
    with pytest.raises(TypeError):
        DryRunPolicy(enabled="yes")  # type: ignore[arg-type]


def test_from_config_none_returns_defaults():
    policy = DryRunPolicy.from_config(None)
    assert policy.enabled is False


def test_from_config_empty_dict_returns_defaults():
    policy = DryRunPolicy.from_config({})
    assert policy.enabled is False


def test_from_config_sets_enabled():
    policy = DryRunPolicy.from_config({"enabled": True})
    assert policy.enabled is True


# ---------------------------------------------------------------------------
# DryRunRecorder
# ---------------------------------------------------------------------------

def test_recorder_starts_empty():
    rec = DryRunRecorder()
    assert rec.recorded() == []


def test_recorder_records_command():
    rec = DryRunRecorder()
    rec.record("echo hello")
    assert "echo hello" in rec.recorded()


def test_recorder_records_multiple_commands():
    rec = DryRunRecorder()
    rec.record("cmd1")
    rec.record("cmd2")
    assert rec.recorded() == ["cmd1", "cmd2"]


def test_recorder_clear_empties_list():
    rec = DryRunRecorder()
    rec.record("cmd")
    rec.clear()
    assert rec.recorded() == []


def test_recorder_returns_copy():
    rec = DryRunRecorder()
    rec.record("cmd")
    result = rec.recorded()
    result.append("injected")
    assert len(rec.recorded()) == 1


# ---------------------------------------------------------------------------
# make_dry_run_result
# ---------------------------------------------------------------------------

def test_make_dry_run_result_exit_code_zero():
    result = make_dry_run_result("echo hi")
    assert result.exit_code == 0


def test_make_dry_run_result_command_stored():
    result = make_dry_run_result("backup.sh")
    assert result.command == "backup.sh"


def test_make_dry_run_result_stdout_indicates_dry_run():
    result = make_dry_run_result("any-cmd")
    assert "dry-run" in result.stdout


def test_make_dry_run_result_duration_is_zero():
    result = make_dry_run_result("any-cmd")
    assert result.duration == 0.0
