"""Tests for cronwatch.redact."""

import pytest
from cronwatch.redact import RedactPolicy, REDACTED


def test_redact_policy_defaults():
    policy = RedactPolicy()
    assert policy.enabled is True
    assert policy.patterns == []


def test_redact_policy_invalid_patterns_raises():
    with pytest.raises(TypeError):
        RedactPolicy(patterns="not-a-list")


def test_redact_password_in_output():
    policy = RedactPolicy()
    result = policy.redact("connecting with password=s3cr3t to db")
    assert "s3cr3t" not in result
    assert REDACTED in result


def test_redact_token_in_output():
    policy = RedactPolicy()
    result = policy.redact("auth token=abc123xyz")
    assert "abc123xyz" not in result
    assert REDACTED in result


def test_redact_secret_in_output():
    policy = RedactPolicy()
    result = policy.redact("using secret=my-secret-value")
    assert "my-secret-value" not in result
    assert REDACTED in result


def test_redact_api_key_in_output():
    policy = RedactPolicy()
    result = policy.redact("api_key=ABCDEF123456")
    assert "ABCDEF123456" not in result
    assert REDACTED in result


def test_redact_custom_pattern():
    policy = RedactPolicy(patterns=[r"(?i)myfield=[^\s]+"])
    result = policy.redact("myfield=supersensitive")
    assert "supersensitive" not in result
    assert REDACTED in result


def test_redact_disabled_leaves_text_unchanged():
    policy = RedactPolicy(enabled=False)
    text = "password=plaintext"
    assert policy.redact(text) == text


def test_redact_empty_string_returns_empty():
    policy = RedactPolicy()
    assert policy.redact("") == ""


def test_redact_none_safe():
    policy = RedactPolicy()
    assert policy.redact(None) is None


def test_from_config_with_extra_patterns():
    cfg = {"redact": {"patterns": [r"(?i)dbpass=[^\s]+"], "enabled": True}}
    policy = RedactPolicy.from_config(cfg)
    assert policy.enabled is True
    result = policy.redact("dbpass=hunter2")
    assert "hunter2" not in result


def test_from_config_disabled():
    cfg = {"redact": {"enabled": False}}
    policy = RedactPolicy.from_config(cfg)
    assert policy.enabled is False


def test_from_config_empty_section():
    policy = RedactPolicy.from_config({})
    assert policy.enabled is True
    assert policy.patterns == []
