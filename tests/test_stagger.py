"""Tests for cronwatch.stagger."""
import pytest
from cronwatch.stagger import StaggerPolicy


def test_stagger_policy_defaults():
    p = StaggerPolicy()
    assert p.window_seconds == 0
    assert p.seed is None
    assert p.enabled is False


def test_stagger_policy_with_window():
    p = StaggerPolicy(window_seconds=60)
    assert p.window_seconds == 60
    assert p.enabled is True


def test_stagger_policy_negative_raises():
    with pytest.raises(ValueError, match=">= 0"):
        StaggerPolicy(window_seconds=-1)


def test_stagger_policy_zero_disables():
    p = StaggerPolicy(window_seconds=0)
    assert p.enabled is False


def test_stagger_policy_invalid_window_type_raises():
    with pytest.raises(TypeError):
        StaggerPolicy(window_seconds="60")  # type: ignore[arg-type]


def test_stagger_policy_invalid_seed_type_raises():
    with pytest.raises(TypeError):
        StaggerPolicy(window_seconds=30, seed=123)  # type: ignore[arg-type]


def test_from_config_none_returns_defaults():
    p = StaggerPolicy.from_config(None)
    assert p.window_seconds == 0
    assert p.seed is None


def test_from_config_empty_dict_returns_defaults():
    p = StaggerPolicy.from_config({})
    assert p.window_seconds == 0


def test_from_config_sets_fields():
    p = StaggerPolicy.from_config({"window_seconds": 120, "seed": "myjobs"})
    assert p.window_seconds == 120
    assert p.seed == "myjobs"


def test_delay_for_disabled_returns_zero():
    p = StaggerPolicy(window_seconds=0)
    assert p.delay_for("backup") == 0.0


def test_delay_for_is_within_window():
    p = StaggerPolicy(window_seconds=300)
    delay = p.delay_for("my_job")
    assert 0.0 <= delay <= 300.0


def test_delay_for_is_deterministic():
    p = StaggerPolicy(window_seconds=300, seed="test")
    d1 = p.delay_for("job_a")
    d2 = p.delay_for("job_a")
    assert d1 == d2


def test_delay_for_differs_by_job_name():
    p = StaggerPolicy(window_seconds=3600, seed="seed")
    delays = {p.delay_for(f"job_{i}") for i in range(10)}
    # With 10 different names across a 3600-second window, very unlikely all equal
    assert len(delays) > 1


def test_delay_for_differs_by_seed():
    p1 = StaggerPolicy(window_seconds=300, seed="alpha")
    p2 = StaggerPolicy(window_seconds=300, seed="beta")
    # Different seeds should produce different delays for the same job
    assert p1.delay_for("backup") != p2.delay_for("backup")


def test_apply_disabled_does_not_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: slept.append(s))
    p = StaggerPolicy(window_seconds=0)
    p.apply("job")
    assert slept == []


def test_apply_enabled_calls_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr("cronwatch.stagger.time.sleep", lambda s: slept.append(s))
    p = StaggerPolicy(window_seconds=60, seed="s")
    p.apply("my_job")
    assert len(slept) == 1
    assert 0.0 <= slept[0] <= 60.0
