"""Tests for cronwatch.precheck."""
import pytest
from cronwatch.precheck import PrecheckPolicy, PrecheckFailedError


def test_precheck_policy_defaults():
    p = PrecheckPolicy()
    assert p.checks == []
    assert p.enabled is False


def test_precheck_policy_with_checks():
    p = PrecheckPolicy(checks=["true", "echo ok"])
    assert p.checks == ["true", "echo ok"]
    assert p.enabled is True


def test_precheck_policy_invalid_checks_type_raises():
    with pytest.raises(TypeError):
        PrecheckPolicy(checks="not-a-list")  # type: ignore


def test_precheck_policy_empty_string_raises():
    with pytest.raises(ValueError):
        PrecheckPolicy(checks=[""])


def test_precheck_policy_whitespace_only_raises():
    with pytest.raises(ValueError):
        PrecheckPolicy(checks=["   "])


def test_precheck_policy_strips_whitespace():
    p = PrecheckPolicy(checks=["  true  "])
    assert p.checks == ["true"]


def test_from_config_none_returns_defaults():
    p = PrecheckPolicy.from_config(None)
    assert p.checks == []


def test_from_config_empty_dict_returns_defaults():
    p = PrecheckPolicy.from_config({})
    assert p.checks == []


def test_from_config_sets_checks():
    p = PrecheckPolicy.from_config({"checks": ["true"]})
    assert p.checks == ["true"]


def test_run_passes_when_all_checks_succeed():
    p = PrecheckPolicy(checks=["true"])
    p.run("myjob")  # should not raise


def test_run_raises_when_check_fails():
    p = PrecheckPolicy(checks=["false"])
    with pytest.raises(PrecheckFailedError) as exc_info:
        p.run("myjob")
    assert "myjob" in str(exc_info.value)
    assert "false" in exc_info.value.failed


def test_run_disabled_policy_does_nothing():
    p = PrecheckPolicy()
    p.run("myjob")  # should not raise


def test_run_collects_all_failures():
    p = PrecheckPolicy(checks=["false", "exit 1"])
    with pytest.raises(PrecheckFailedError) as exc_info:
        p.run("myjob")
    assert len(exc_info.value.failed) == 2


def test_failed_error_contains_job_name():
    err = PrecheckFailedError("myjob", ["false"])
    assert "myjob" in str(err)


def test_failed_error_contains_check_command():
    err = PrecheckFailedError("myjob", ["false"])
    assert "false" in str(err)
