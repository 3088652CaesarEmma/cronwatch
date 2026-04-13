"""Tests for cronwatch.dependency."""

from __future__ import annotations

import pytest

from cronwatch.dependency import (
    DependencyPolicy,
    build_dependency_graph,
    jobs_ready_to_run,
    resolve_order,
)


# ---------------------------------------------------------------------------
# DependencyPolicy
# ---------------------------------------------------------------------------

def test_dependency_policy_defaults():
    policy = DependencyPolicy()
    assert policy.requires == []
    assert policy.enabled() is False


def test_dependency_policy_with_requires():
    policy = DependencyPolicy(requires=["job-a", "job-b"])
    assert policy.requires == ["job-a", "job-b"]
    assert policy.enabled() is True


def test_dependency_policy_strips_whitespace():
    policy = DependencyPolicy(requires=["  job-a  ", " job-b"])
    assert policy.requires == ["job-a", "job-b"]


def test_dependency_policy_invalid_requires_type_raises():
    with pytest.raises(TypeError):
        DependencyPolicy(requires="job-a")  # type: ignore


def test_dependency_policy_empty_string_in_requires_raises():
    with pytest.raises(ValueError):
        DependencyPolicy(requires=["job-a", ""])


def test_from_config_none_returns_defaults():
    policy = DependencyPolicy.from_config(None)
    assert policy.requires == []


def test_from_config_with_requires():
    policy = DependencyPolicy.from_config({"requires": ["setup"]})
    assert policy.requires == ["setup"]


# ---------------------------------------------------------------------------
# build_dependency_graph
# ---------------------------------------------------------------------------

class _FakeJob:
    def __init__(self, name, requires=None):
        self.name = name
        self.dependency = DependencyPolicy(requires=requires or [])


def test_build_dependency_graph_no_deps():
    jobs = [_FakeJob("a"), _FakeJob("b")]
    graph = build_dependency_graph(jobs)
    assert graph == {"a": [], "b": []}


def test_build_dependency_graph_with_deps():
    jobs = [_FakeJob("a"), _FakeJob("b", requires=["a"])]
    graph = build_dependency_graph(jobs)
    assert graph["b"] == ["a"]


# ---------------------------------------------------------------------------
# resolve_order
# ---------------------------------------------------------------------------

def test_resolve_order_simple_chain():
    graph = {"a": [], "b": ["a"], "c": ["b"]}
    order = resolve_order(graph)
    assert order.index("a") < order.index("b") < order.index("c")


def test_resolve_order_no_deps():
    graph = {"x": [], "y": [], "z": []}
    order = resolve_order(graph)
    assert set(order) == {"x", "y", "z"}


def test_resolve_order_circular_raises():
    graph = {"a": ["b"], "b": ["a"]}
    with pytest.raises(ValueError, match="Circular dependency"):
        resolve_order(graph)


def test_resolve_order_unknown_dep_raises():
    graph = {"a": ["missing"]}
    with pytest.raises(ValueError, match="unknown job"):
        resolve_order(graph)


# ---------------------------------------------------------------------------
# jobs_ready_to_run
# ---------------------------------------------------------------------------

def test_jobs_ready_no_deps_all_ready():
    graph = {"a": [], "b": []}
    ready = jobs_ready_to_run(graph, succeeded=set())
    assert set(ready) == {"a", "b"}


def test_jobs_ready_dep_not_yet_succeeded():
    graph = {"a": [], "b": ["a"]}
    ready = jobs_ready_to_run(graph, succeeded=set())
    assert "b" not in ready
    assert "a" in ready


def test_jobs_ready_dep_succeeded():
    graph = {"a": [], "b": ["a"]}
    ready = jobs_ready_to_run(graph, succeeded={"a"})
    assert "b" in ready
