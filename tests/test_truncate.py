"""Tests for cronwatch.truncate."""

import pytest

from cronwatch.truncate import TruncatePolicy, truncate_output


# ---------------------------------------------------------------------------
# TruncatePolicy construction
# ---------------------------------------------------------------------------

def test_truncate_policy_defaults():
    p = TruncatePolicy()
    assert p.max_lines == 100
    assert p.max_bytes == 16_384
    assert p.marker == "... (truncated)"


def test_truncate_policy_custom_values():
    p = TruncatePolicy(max_lines=10, max_bytes=512, marker="[cut]")
    assert p.max_lines == 10
    assert p.max_bytes == 512
    assert p.marker == "[cut]"


def test_truncate_policy_invalid_max_lines():
    with pytest.raises(ValueError, match="max_lines"):
        TruncatePolicy(max_lines=0)


def test_truncate_policy_invalid_max_bytes():
    with pytest.raises(ValueError, match="max_bytes"):
        TruncatePolicy(max_bytes=0)


def test_truncate_policy_enabled_is_true():
    assert TruncatePolicy().enabled is True


def test_truncate_policy_from_config():
    cfg = {"max_lines": 50, "max_bytes": 1024, "marker": "---"}
    p = TruncatePolicy.from_config(cfg)
    assert p.max_lines == 50
    assert p.max_bytes == 1024
    assert p.marker == "---"


def test_truncate_policy_from_config_uses_defaults_for_missing_keys():
    p = TruncatePolicy.from_config({})
    assert p.max_lines == 100
    assert p.max_bytes == 16_384


# ---------------------------------------------------------------------------
# truncate_output
# ---------------------------------------------------------------------------

def test_short_output_unchanged():
    text = "hello\nworld\n"
    assert truncate_output(text) == text


def test_empty_string_unchanged():
    assert truncate_output("") == ""


def test_line_limit_truncates():
    lines = [f"line {i}\n" for i in range(200)]
    text = "".join(lines)
    policy = TruncatePolicy(max_lines=10, max_bytes=10_000)
    result = truncate_output(text, policy)
    result_lines = result.splitlines()
    assert result_lines[-1] == policy.marker
    assert len(result_lines) == 11  # 10 content lines + marker


def test_byte_limit_truncates():
    text = "a" * 200 + "\n"
    policy = TruncatePolicy(max_lines=1000, max_bytes=50)
    result = truncate_output(text, policy)
    assert result.endswith(policy.marker)
    # Byte content before marker must not exceed limit
    content_before_marker = result[: result.rfind(policy.marker)]
    assert len(content_before_marker.encode()) <= 50


def test_marker_appended_only_once_when_both_limits_exceeded():
    lines = [f"line {i}\n" for i in range(200)]
    text = "".join(lines)
    policy = TruncatePolicy(max_lines=5, max_bytes=20)
    result = truncate_output(text, policy)
    assert result.count(policy.marker) == 1


def test_uses_default_policy_when_none_passed():
    text = "ok\n"
    # Should not raise and should return the text unchanged
    assert truncate_output(text, None) == text
