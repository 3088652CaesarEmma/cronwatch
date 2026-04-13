"""Tests for cronwatch.jitter."""

import pytest
from unittest.mock import patch

from cronwatch.jitter import JitterPolicy


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_jitter_policy_defaults():
    p = JitterPolicy()
    assert p.max_seconds == 0
    assert p.enabled is False


def test_jitter_policy_with_seconds():
    p = JitterPolicy(max_seconds=10)
    assert p.max_seconds == 10
    assert p.enabled is True


def test_jitter_policy_negative_raises():
    with pytest.raises(ValueError, match="max_seconds"):
        JitterPolicy(max_seconds=-1)


def test_jitter_policy_zero_disables():
    p = JitterPolicy(max_seconds=0)
    assert p.enabled is False


# ---------------------------------------------------------------------------
# from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    p = JitterPolicy.from_config(None)
    assert p.max_seconds == 0
    assert p.enabled is False


def test_from_config_empty_dict_returns_defaults():
    p = JitterPolicy.from_config({})
    assert p.max_seconds == 0


def test_from_config_sets_max_seconds():
    p = JitterPolicy.from_config({"max_seconds": 30})
    assert p.max_seconds == 30
    assert p.enabled is True


# ---------------------------------------------------------------------------
# sample / apply
# ---------------------------------------------------------------------------

def test_sample_returns_zero_when_disabled():
    p = JitterPolicy(max_seconds=0)
    assert p.sample() == 0.0


def test_sample_within_range():
    p = JitterPolicy(max_seconds=5)
    for _ in range(20):
        v = p.sample()
        assert 0.0 <= v <= 5.0


def test_apply_sleeps_when_enabled():
    p = JitterPolicy(max_seconds=10)
    with patch("cronwatch.jitter.time.sleep") as mock_sleep, \
         patch("cronwatch.jitter.random.uniform", return_value=3.7):
        delay = p.apply()
    mock_sleep.assert_called_once_with(3.7)
    assert delay == pytest.approx(3.7)


def test_apply_does_not_sleep_when_disabled():
    p = JitterPolicy(max_seconds=0)
    with patch("cronwatch.jitter.time.sleep") as mock_sleep:
        delay = p.apply()
    mock_sleep.assert_not_called()
    assert delay == 0.0
