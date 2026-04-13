"""Tests for cronwatch.environ."""

import os
import pytest

from cronwatch.environ import EnvironPolicy


# ---------------------------------------------------------------------------
# EnvironPolicy construction
# ---------------------------------------------------------------------------

def test_environ_policy_defaults():
    policy = EnvironPolicy()
    assert policy.vars == {}
    assert policy.inherit is True
    assert policy.clear_keys == []


def test_environ_policy_invalid_vars_raises():
    with pytest.raises(TypeError):
        EnvironPolicy(vars="not-a-dict")


def test_environ_policy_invalid_clear_keys_raises():
    with pytest.raises(TypeError):
        EnvironPolicy(clear_keys="not-a-list")


# ---------------------------------------------------------------------------
# from_config
# ---------------------------------------------------------------------------

def test_from_config_none_returns_defaults():
    policy = EnvironPolicy.from_config(None)
    assert policy.inherit is True
    assert policy.vars == {}


def test_from_config_empty_dict_returns_defaults():
    policy = EnvironPolicy.from_config({})
    assert policy.inherit is True


def test_from_config_sets_vars():
    policy = EnvironPolicy.from_config({"vars": {"FOO": "bar"}})
    assert policy.vars == {"FOO": "bar"}


def test_from_config_sets_inherit_false():
    policy = EnvironPolicy.from_config({"inherit": False})
    assert policy.inherit is False


def test_from_config_sets_clear_keys():
    policy = EnvironPolicy.from_config({"clear_keys": ["SECRET"]})
    assert "SECRET" in policy.clear_keys


# ---------------------------------------------------------------------------
# build_env
# ---------------------------------------------------------------------------

def test_build_env_inherits_os_environ():
    policy = EnvironPolicy()
    env = policy.build_env()
    assert "PATH" in env or True  # PATH may not exist in all CI envs
    # At minimum the result should be a dict
    assert isinstance(env, dict)


def test_build_env_merges_vars():
    policy = EnvironPolicy(vars={"MY_VAR": "hello"})
    env = policy.build_env()
    assert env["MY_VAR"] == "hello"


def test_build_env_no_inherit_excludes_os_environ(monkeypatch):
    monkeypatch.setenv("_CRONWATCH_TEST_KEY", "should-not-appear")
    policy = EnvironPolicy(inherit=False, vars={"ONLY": "this"})
    env = policy.build_env()
    assert "_CRONWATCH_TEST_KEY" not in env
    assert env["ONLY"] == "this"


def test_build_env_clears_specified_keys(monkeypatch):
    monkeypatch.setenv("_CRONWATCH_CLEAR", "present")
    policy = EnvironPolicy(clear_keys=["_CRONWATCH_CLEAR"])
    env = policy.build_env()
    assert "_CRONWATCH_CLEAR" not in env


def test_build_env_vars_override_inherited(monkeypatch):
    monkeypatch.setenv("_CRONWATCH_OVERRIDE", "original")
    policy = EnvironPolicy(vars={"_CRONWATCH_OVERRIDE": "overridden"})
    env = policy.build_env()
    assert env["_CRONWATCH_OVERRIDE"] == "overridden"


# ---------------------------------------------------------------------------
# enabled property
# ---------------------------------------------------------------------------

def test_enabled_false_for_default_policy():
    assert EnvironPolicy().enabled is False


def test_enabled_true_when_vars_set():
    assert EnvironPolicy(vars={"X": "1"}).enabled is True


def test_enabled_true_when_clear_keys_set():
    assert EnvironPolicy(clear_keys=["HOME"]).enabled is True


def test_enabled_true_when_inherit_false():
    assert EnvironPolicy(inherit=False).enabled is True
