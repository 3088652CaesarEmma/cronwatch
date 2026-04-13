"""Tests for cronwatch.label."""
import pytest
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.label import (
    LabelPolicy,
    collect_label_values,
    filter_by_label_selector,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeJob:
    name: str
    label_policy: Optional[LabelPolicy] = field(default=None)


# ---------------------------------------------------------------------------
# LabelPolicy construction
# ---------------------------------------------------------------------------

def test_label_policy_defaults():
    p = LabelPolicy()
    assert p.labels == {}
    assert p.enabled() is False


def test_label_policy_with_labels():
    p = LabelPolicy(labels={"env": "prod", "team": "ops"})
    assert p.enabled() is True
    assert p.get("env") == "prod"


def test_label_policy_get_missing_key_returns_none():
    p = LabelPolicy(labels={"env": "prod"})
    assert p.get("missing") is None


def test_label_policy_invalid_labels_raises():
    with pytest.raises(ValueError):
        LabelPolicy(labels="not-a-dict")  # type: ignore[arg-type]


def test_label_policy_non_string_values_raises():
    with pytest.raises(ValueError):
        LabelPolicy(labels={"env": 42})  # type: ignore[dict-item]


# ---------------------------------------------------------------------------
# from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    p = LabelPolicy.from_config(None)
    assert p.labels == {}


def test_from_config_empty_dict_returns_defaults():
    p = LabelPolicy.from_config({})
    assert p.labels == {}


def test_from_config_with_labels():
    p = LabelPolicy.from_config({"labels": {"env": "staging"}})
    assert p.get("env") == "staging"


def test_from_config_invalid_labels_raises():
    with pytest.raises(ValueError):
        LabelPolicy.from_config({"labels": "bad"})


# ---------------------------------------------------------------------------
# matches
# ---------------------------------------------------------------------------

def test_matches_all_present():
    p = LabelPolicy(labels={"env": "prod", "team": "ops"})
    assert p.matches({"env": "prod"}) is True


def test_matches_partial_selector():
    p = LabelPolicy(labels={"env": "prod", "team": "ops"})
    assert p.matches({"env": "prod", "team": "ops"}) is True


def test_matches_wrong_value_returns_false():
    p = LabelPolicy(labels={"env": "prod"})
    assert p.matches({"env": "dev"}) is False


def test_matches_missing_key_returns_false():
    p = LabelPolicy(labels={"env": "prod"})
    assert p.matches({"team": "ops"}) is False


# ---------------------------------------------------------------------------
# filter_by_label_selector
# ---------------------------------------------------------------------------

def _make_jobs():
    return [
        _FakeJob("job-a", LabelPolicy(labels={"env": "prod", "team": "ops"})),
        _FakeJob("job-b", LabelPolicy(labels={"env": "dev", "team": "ops"})),
        _FakeJob("job-c", LabelPolicy(labels={"env": "prod", "team": "qa"})),
        _FakeJob("job-d"),  # no label_policy
    ]


def test_filter_by_label_selector_single_match():
    jobs = _make_jobs()
    result = filter_by_label_selector(jobs, {"env": "dev"})
    assert [j.name for j in result] == ["job-b"]


def test_filter_by_label_selector_multiple_matches():
    jobs = _make_jobs()
    result = filter_by_label_selector(jobs, {"team": "ops"})
    assert [j.name for j in result] == ["job-a", "job-b"]


def test_filter_by_label_selector_no_match():
    jobs = _make_jobs()
    result = filter_by_label_selector(jobs, {"env": "staging"})
    assert result == []


def test_filter_skips_jobs_without_label_policy():
    jobs = _make_jobs()
    result = filter_by_label_selector(jobs, {"env": "prod"})
    names = [j.name for j in result]
    assert "job-d" not in names


# ---------------------------------------------------------------------------
# collect_label_values
# ---------------------------------------------------------------------------

def test_collect_label_values_unique():
    jobs = _make_jobs()
    values = collect_label_values(jobs, "env")
    assert sorted(values) == ["dev", "prod"]


def test_collect_label_values_missing_key():
    jobs = _make_jobs()
    values = collect_label_values(jobs, "nonexistent")
    assert values == []
