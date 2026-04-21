"""Tests for cronwatch.skip (SkipPolicy and JobSkippedError)."""
import pytest

from cronwatch.skip import JobSkippedError, SkipPolicy


# ---------------------------------------------------------------------------
# SkipPolicy defaults
# ---------------------------------------------------------------------------

def test_skip_policy_defaults():
    p = SkipPolicy()
    assert p.skip_if is None
    assert p.timeout == 10
    assert p.shell is True


def test_skip_policy_enabled_when_skip_if_set():
    p = SkipPolicy(skip_if="true")
    assert p.enabled is True


def test_skip_policy_disabled_when_no_skip_if():
    p = SkipPolicy()
    assert p.enabled is False


def test_skip_policy_empty_string_becomes_none():
    p = SkipPolicy(skip_if="")
    assert p.skip_if is None
    assert p.enabled is False


def test_skip_policy_invalid_skip_if_type_raises():
    with pytest.raises(TypeError):
        SkipPolicy(skip_if=123)


def test_skip_policy_invalid_timeout_raises():
    with pytest.raises(ValueError):
        SkipPolicy(skip_if="true", timeout=0)


def test_skip_policy_negative_timeout_raises():
    with pytest.raises(ValueError):
        SkipPolicy(skip_if="true", timeout=-5)


# ---------------------------------------------------------------------------
# from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    p = SkipPolicy.from_config(None)
    assert p.skip_if is None


def test_from_config_empty_dict_returns_defaults():
    p = SkipPolicy.from_config({})
    assert p.skip_if is None


def test_from_config_sets_skip_if():
    p = SkipPolicy.from_config({"skip_if": "test -f /tmp/skip"})
    assert p.skip_if == "test -f /tmp/skip"


def test_from_config_sets_timeout():
    p = SkipPolicy.from_config({"skip_if": "true", "timeout": 5})
    assert p.timeout == 5


# ---------------------------------------------------------------------------
# should_skip
# ---------------------------------------------------------------------------

def test_should_skip_returns_false_when_disabled():
    p = SkipPolicy()
    assert p.should_skip() is False


def test_should_skip_true_when_command_exits_zero():
    p = SkipPolicy(skip_if="true")  # POSIX 'true' always exits 0
    assert p.should_skip() is True


def test_should_skip_false_when_command_exits_nonzero():
    p = SkipPolicy(skip_if="false")  # POSIX 'false' always exits 1
    assert p.should_skip() is False


def test_should_skip_false_on_timeout():
    # Use a very short timeout so the sleep command exceeds it
    p = SkipPolicy(skip_if="sleep 10", timeout=1)
    assert p.should_skip() is False


# ---------------------------------------------------------------------------
# JobSkippedError
# ---------------------------------------------------------------------------

def test_job_skipped_error_message():
    err = JobSkippedError("myjob", "condition met")
    assert "myjob" in str(err)
    assert "condition met" in str(err)


def test_job_skipped_error_attributes():
    err = JobSkippedError("backup", "disk not mounted")
    assert err.job_name == "backup"
    assert err.reason == "disk not mounted"
