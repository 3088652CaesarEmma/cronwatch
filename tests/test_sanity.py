"""Tests for cronwatch.sanity."""
import pytest

from cronwatch.sanity import SanityCheckError, SanityPolicy


# ---------------------------------------------------------------------------
# SanityPolicy construction
# ---------------------------------------------------------------------------

def test_sanity_policy_defaults():
    policy = SanityPolicy()
    assert policy.checks == []
    assert policy.timeout == 10
    assert policy.enabled is False


def test_sanity_policy_with_checks():
    policy = SanityPolicy(checks=["true", "echo ok"])
    assert len(policy.checks) == 2
    assert policy.enabled is True


def test_sanity_policy_invalid_checks_type_raises():
    with pytest.raises(TypeError):
        SanityPolicy(checks="not-a-list")


def test_sanity_policy_empty_string_check_raises():
    with pytest.raises(ValueError):
        SanityPolicy(checks=[""])


def test_sanity_policy_whitespace_only_check_raises():
    with pytest.raises(ValueError):
        SanityPolicy(checks=["   "])


def test_sanity_policy_invalid_timeout_raises():
    with pytest.raises(ValueError):
        SanityPolicy(checks=["true"], timeout=0)


def test_sanity_policy_negative_timeout_raises():
    with pytest.raises(ValueError):
        SanityPolicy(checks=["true"], timeout=-5)


# ---------------------------------------------------------------------------
# from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    policy = SanityPolicy.from_config(None)
    assert policy.checks == []
    assert policy.timeout == 10


def test_from_config_empty_dict_returns_defaults():
    policy = SanityPolicy.from_config({})
    assert policy.checks == []


def test_from_config_sets_checks_and_timeout():
    policy = SanityPolicy.from_config({"checks": ["true"], "timeout": 5})
    assert policy.checks == ["true"]
    assert policy.timeout == 5


# ---------------------------------------------------------------------------
# run_checks — integration with real subprocesses
# ---------------------------------------------------------------------------

def test_run_checks_passes_for_true():
    policy = SanityPolicy(checks=["true"])
    # Should not raise
    policy.run_checks("my_job")


def test_run_checks_raises_on_false():
    policy = SanityPolicy(checks=["false"])
    with pytest.raises(SanityCheckError) as exc_info:
        policy.run_checks("my_job")
    err = exc_info.value
    assert err.job_name == "my_job"
    assert err.check == "false"
    assert err.exit_code != 0


def test_run_checks_stops_at_first_failure():
    policy = SanityPolicy(checks=["false", "true"])
    with pytest.raises(SanityCheckError) as exc_info:
        policy.run_checks("job")
    assert exc_info.value.check == "false"


def test_sanity_check_error_message_contains_job_name():
    err = SanityCheckError("nightly_backup", "ping -c1 db", 1)
    assert "nightly_backup" in str(err)
    assert "ping -c1 db" in str(err)


def test_run_checks_disabled_policy_does_nothing():
    policy = SanityPolicy()  # no checks
    policy.run_checks("job")  # must not raise
