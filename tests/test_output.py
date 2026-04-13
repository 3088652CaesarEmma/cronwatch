"""Tests for cronwatch.output module."""

import pytest

from cronwatch.output import OutputPolicy, process_output, process_result_output
from cronwatch.truncate import TruncatePolicy
from cronwatch.redact import RedactPolicy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_policy() -> OutputPolicy:
    return OutputPolicy()


@pytest.fixture
def truncating_policy() -> OutputPolicy:
    return OutputPolicy(truncate=TruncatePolicy(max_lines=3, max_bytes=0))


@pytest.fixture
def redacting_policy() -> OutputPolicy:
    return OutputPolicy(redact=RedactPolicy(patterns=[r"secret\w*"]))


# ---------------------------------------------------------------------------
# OutputPolicy construction
# ---------------------------------------------------------------------------

def test_output_policy_defaults():
    policy = OutputPolicy()
    assert isinstance(policy.truncate, TruncatePolicy)
    assert isinstance(policy.redact, RedactPolicy)


def test_output_policy_from_config_empty():
    policy = OutputPolicy.from_config({})
    assert isinstance(policy.truncate, TruncatePolicy)
    assert isinstance(policy.redact, RedactPolicy)


def test_output_policy_from_config_with_truncate():
    policy = OutputPolicy.from_config({"truncate": {"max_lines": 5}})
    assert policy.truncate.max_lines == 5


def test_output_policy_from_config_with_redact():
    policy = OutputPolicy.from_config({"redact": {"patterns": [r"token\w*"]}})
    assert r"token\w*" in policy.redact.patterns


# ---------------------------------------------------------------------------
# process_output
# ---------------------------------------------------------------------------

def test_process_output_none_returns_empty(default_policy):
    assert process_output(None, default_policy) == ""


def test_process_output_passthrough(default_policy):
    assert process_output("hello world", default_policy) == "hello world"


def test_process_output_truncates(truncating_policy):
    lines = "\n".join(f"line{i}" for i in range(10))
    result = process_output(lines, truncating_policy)
    assert result.count("\n") < lines.count("\n")


def test_process_output_redacts(redacting_policy):
    result = process_output("found secretToken here", redacting_policy)
    assert "secretToken" not in result


def test_process_output_empty_string(default_policy):
    assert process_output("", default_policy) == ""


# ---------------------------------------------------------------------------
# process_result_output
# ---------------------------------------------------------------------------

def test_process_result_output_returns_tuple(default_policy):
    out, err = process_result_output("stdout text", "stderr text", default_policy)
    assert out == "stdout text"
    assert err == "stderr text"


def test_process_result_output_handles_none(default_policy):
    out, err = process_result_output(None, None, default_policy)
    assert out == ""
    assert err == ""


def test_process_result_output_redacts_both():
    policy = OutputPolicy(redact=RedactPolicy(patterns=[r"pass\w*"]))
    out, err = process_result_output("password=abc", "pass123 leaked", policy)
    assert "password" not in out
    assert "pass123" not in err
