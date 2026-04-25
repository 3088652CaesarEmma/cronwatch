"""Tests for cronwatch.splay."""

import pytest
from unittest.mock import patch

from cronwatch.splay import SplayPolicy


def test_splay_policy_defaults():
    p = SplayPolicy()
    assert p.window == 0.0
    assert p.seed is None
    assert p.enabled is False


def test_splay_policy_with_window():
    p = SplayPolicy(window=30)
    assert p.window == 30.0
    assert p.enabled is True


def test_splay_policy_negative_raises():
    with pytest.raises(ValueError, match=">= 0"):
        SplayPolicy(window=-1)


def test_splay_policy_zero_disables():
    p = SplayPolicy(window=0)
    assert p.enabled is False


def test_splay_policy_invalid_window_type_raises():
    with pytest.raises(TypeError, match="number"):
        SplayPolicy(window="fast")


def test_from_config_none_returns_defaults():
    p = SplayPolicy.from_config(None)
    assert p.window == 0.0
    assert p.enabled is False


def test_from_config_empty_dict_returns_defaults():
    p = SplayPolicy.from_config({})
    assert p.window == 0.0


def test_from_config_sets_window():
    p = SplayPolicy.from_config({"window": 60})
    assert p.window == 60.0
    assert p.enabled is True


def test_from_config_sets_seed():
    p = SplayPolicy.from_config({"window": 10, "seed": 42})
    assert p.seed == 42


def test_sample_disabled_returns_zero():
    p = SplayPolicy(window=0)
    assert p.sample() == 0.0


def test_sample_within_window():
    p = SplayPolicy(window=10.0)
    for _ in range(50):
        d = p.sample()
        assert 0.0 <= d < 10.0


def test_sample_deterministic_with_seed():
    p1 = SplayPolicy(window=20, seed=7)
    p2 = SplayPolicy(window=20, seed=7)
    assert p1.sample() == p2.sample()


def test_apply_disabled_does_not_sleep():
    p = SplayPolicy(window=0)
    with patch("cronwatch.splay.time.sleep") as mock_sleep:
        delay = p.apply()
    mock_sleep.assert_not_called()
    assert delay == 0.0


def test_apply_enabled_sleeps():
    p = SplayPolicy(window=5, seed=99)
    expected = p.sample()
    with patch("cronwatch.splay.time.sleep") as mock_sleep:
        delay = p.apply()
    mock_sleep.assert_called_once_with(pytest.approx(expected))
    assert delay == pytest.approx(expected)


def test_apply_returns_delay_amount():
    p = SplayPolicy(window=3, seed=1)
    with patch("cronwatch.splay.time.sleep"):
        delay = p.apply()
    assert 0.0 <= delay < 3.0
