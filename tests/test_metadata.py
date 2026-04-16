"""Tests for cronwatch.metadata."""
import pytest
from cronwatch.metadata import MetadataPolicy


def test_metadata_policy_defaults():
    p = MetadataPolicy()
    assert p.labels == {}
    assert p.enabled() is False


def test_metadata_policy_with_labels():
    p = MetadataPolicy(labels={"env": "prod", "team": "ops"})
    assert p.get("env") == "prod"
    assert p.get("team") == "ops"
    assert p.enabled() is True


def test_metadata_policy_get_missing_returns_default():
    p = MetadataPolicy(labels={"x": 1})
    assert p.get("missing") is None
    assert p.get("missing", "fallback") == "fallback"


def test_metadata_policy_invalid_labels_type_raises():
    with pytest.raises(TypeError):
        MetadataPolicy(labels="not-a-dict")


def test_metadata_policy_empty_key_raises():
    with pytest.raises(ValueError):
        MetadataPolicy(labels={"": "value"})


def test_metadata_policy_set_adds_key():
    p = MetadataPolicy()
    p.set("owner", "alice")
    assert p.get("owner") == "alice"


def test_metadata_policy_set_empty_key_raises():
    p = MetadataPolicy()
    with pytest.raises(ValueError):
        p.set("", "value")


def test_metadata_policy_merge_combines_labels():
    a = MetadataPolicy(labels={"a": 1, "b": 2})
    b = MetadataPolicy(labels={"b": 99, "c": 3})
    merged = a.merge(b)
    assert merged.get("a") == 1
    assert merged.get("b") == 99
    assert merged.get("c") == 3


def test_metadata_policy_merge_does_not_mutate_originals():
    a = MetadataPolicy(labels={"x": 1})
    b = MetadataPolicy(labels={"x": 2})
    a.merge(b)
    assert a.get("x") == 1


def test_metadata_policy_as_dict_returns_copy():
    p = MetadataPolicy(labels={"k": "v"})
    d = p.as_dict()
    d["k"] = "changed"
    assert p.get("k") == "v"


def test_from_config_none_returns_defaults():
    p = MetadataPolicy.from_config(None)
    assert p.labels == {}


def test_from_config_empty_dict_returns_defaults():
    p = MetadataPolicy.from_config({})
    assert p.labels == {}


def test_from_config_with_labels():
    p = MetadataPolicy.from_config({"labels": {"env": "staging"}})
    assert p.get("env") == "staging"


def test_from_config_invalid_labels_type_raises():
    with pytest.raises(TypeError):
        MetadataPolicy.from_config({"labels": ["not", "a", "dict"]})
