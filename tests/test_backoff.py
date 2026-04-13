"""Tests for cronwatch.backoff."""

import pytest
from cronwatch.backoff import BackoffPolicy


def test_backoff_policy_defaults():
    bp = BackoffPolicy()
    assert bp.base_delay == 1.0
    assert bp.multiplier == 2.0
    assert bp.max_delay == 300.0
    assert bp.jitter == 0.0


def test_backoff_policy_invalid_base_delay_raises():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffPolicy(base_delay=-1.0)


def test_backoff_policy_invalid_multiplier_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffPolicy(multiplier=0.5)


def test_backoff_policy_max_delay_less_than_base_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffPolicy(base_delay=10.0, max_delay=5.0)


def test_backoff_policy_invalid_jitter_raises():
    with pytest.raises(ValueError, match="jitter"):
        BackoffPolicy(jitter=1.5)


def test_delay_for_attempt_zero_returns_base():
    bp = BackoffPolicy(base_delay=2.0, multiplier=2.0)
    assert bp.delay_for(0) == pytest.approx(2.0)


def test_delay_for_attempt_one_doubles():
    bp = BackoffPolicy(base_delay=2.0, multiplier=2.0)
    assert bp.delay_for(1) == pytest.approx(4.0)


def test_delay_for_attempt_two_quadruples():
    bp = BackoffPolicy(base_delay=2.0, multiplier=2.0)
    assert bp.delay_for(2) == pytest.approx(8.0)


def test_delay_capped_at_max_delay():
    bp = BackoffPolicy(base_delay=1.0, multiplier=10.0, max_delay=50.0)
    assert bp.delay_for(3) == pytest.approx(50.0)


def test_delay_for_negative_attempt_raises():
    bp = BackoffPolicy()
    with pytest.raises(ValueError, match="attempt"):
        bp.delay_for(-1)


def test_delays_returns_correct_length():
    bp = BackoffPolicy(base_delay=1.0, multiplier=2.0)
    result = bp.delays(4)
    assert len(result) == 4


def test_delays_values_are_increasing():
    bp = BackoffPolicy(base_delay=1.0, multiplier=3.0)
    result = bp.delays(3)
    assert result[0] < result[1] < result[2]


def test_enabled_true_when_base_delay_positive():
    bp = BackoffPolicy(base_delay=1.0)
    assert bp.enabled is True


def test_enabled_false_when_base_delay_zero():
    bp = BackoffPolicy(base_delay=0.0)
    assert bp.enabled is False


def test_from_config_none_returns_defaults():
    bp = BackoffPolicy.from_config(None)
    assert bp.base_delay == 1.0
    assert bp.multiplier == 2.0


def test_from_config_custom_values():
    bp = BackoffPolicy.from_config({"base_delay": 5.0, "multiplier": 3.0, "max_delay": 600.0})
    assert bp.base_delay == pytest.approx(5.0)
    assert bp.multiplier == pytest.approx(3.0)
    assert bp.max_delay == pytest.approx(600.0)
