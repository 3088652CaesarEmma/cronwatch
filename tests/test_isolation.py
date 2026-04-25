"""Tests for cronwatch.isolation."""

import os
import shutil
import pytest

from cronwatch.isolation import IsolationPolicy


def test_isolation_policy_defaults():
    policy = IsolationPolicy()
    assert policy.use_tmpdir is False
    assert policy.clean_env is False
    assert policy.allowed_vars == []
    assert policy.enabled is False


def test_isolation_policy_enabled_when_use_tmpdir():
    policy = IsolationPolicy(use_tmpdir=True)
    assert policy.enabled is True


def test_isolation_policy_enabled_when_clean_env():
    policy = IsolationPolicy(clean_env=True)
    assert policy.enabled is True


def test_isolation_policy_invalid_use_tmpdir_raises():
    with pytest.raises(TypeError):
        IsolationPolicy(use_tmpdir="yes")


def test_isolation_policy_invalid_clean_env_raises():
    with pytest.raises(TypeError):
        IsolationPolicy(clean_env=1)


def test_isolation_policy_invalid_allowed_vars_type_raises():
    with pytest.raises(TypeError):
        IsolationPolicy(allowed_vars="PATH")


def test_isolation_policy_empty_string_in_allowed_vars_raises():
    with pytest.raises(ValueError):
        IsolationPolicy(allowed_vars=[""])


def test_isolation_policy_whitespace_only_in_allowed_vars_raises():
    with pytest.raises(ValueError):
        IsolationPolicy(allowed_vars=["   "])


def test_isolation_policy_strips_allowed_vars():
    policy = IsolationPolicy(allowed_vars=[" PATH ", " HOME"])
    assert policy.allowed_vars == ["PATH", "HOME"]


def test_from_config_none_returns_defaults():
    policy = IsolationPolicy.from_config(None)
    assert policy.use_tmpdir is False
    assert policy.clean_env is False


def test_from_config_empty_dict_returns_defaults():
    policy = IsolationPolicy.from_config({})
    assert policy.enabled is False


def test_from_config_sets_use_tmpdir():
    policy = IsolationPolicy.from_config({"use_tmpdir": True})
    assert policy.use_tmpdir is True


def test_from_config_sets_clean_env_and_allowed_vars():
    policy = IsolationPolicy.from_config({"clean_env": True, "allowed_vars": ["PATH", "HOME"]})
    assert policy.clean_env is True
    assert "PATH" in policy.allowed_vars


def test_build_env_returns_none_when_clean_env_false():
    policy = IsolationPolicy()
    assert policy.build_env() is None


def test_build_env_filters_to_allowed_vars(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SECRET", "hunter2")
    policy = IsolationPolicy(clean_env=True, allowed_vars=["PATH"])
    env = policy.build_env()
    assert "PATH" in env
    assert "SECRET" not in env


def test_make_workdir_returns_none_when_disabled():
    policy = IsolationPolicy()
    assert policy.make_workdir() is None


def test_make_workdir_creates_directory():
    policy = IsolationPolicy(use_tmpdir=True)
    tmpdir = policy.make_workdir()
    try:
        assert tmpdir is not None
        assert os.path.isdir(tmpdir)
        assert "cronwatch_" in tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
