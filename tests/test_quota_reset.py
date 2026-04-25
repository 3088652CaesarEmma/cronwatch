"""Tests for cronwatch.quota_reset."""
import json
import time
from pathlib import Path

import pytest

from cronwatch.quota_reset import (
    QuotaResetPolicy,
    get_quota_reset_state_path,
    load_quota_reset_state,
    record_reset,
    save_quota_reset_state,
    should_reset,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# QuotaResetPolicy
# ---------------------------------------------------------------------------

def test_quota_reset_policy_defaults():
    p = QuotaResetPolicy()
    assert p.reset_after == 0
    assert p.reset_on_success is False
    assert p.enabled is False


def test_quota_reset_policy_enabled_when_reset_after_nonzero():
    p = QuotaResetPolicy(reset_after=3600)
    assert p.enabled is True


def test_quota_reset_policy_enabled_when_reset_on_success():
    p = QuotaResetPolicy(reset_on_success=True)
    assert p.enabled is True


def test_quota_reset_policy_negative_reset_after_raises():
    with pytest.raises(ValueError):
        QuotaResetPolicy(reset_after=-1)


def test_quota_reset_policy_invalid_reset_on_success_raises():
    with pytest.raises(TypeError):
        QuotaResetPolicy(reset_on_success="yes")  # type: ignore[arg-type]


def test_from_config_none_returns_defaults():
    p = QuotaResetPolicy.from_config(None)
    assert p.reset_after == 0
    assert p.reset_on_success is False


def test_from_config_sets_fields():
    p = QuotaResetPolicy.from_config({"reset_after": 7200, "reset_on_success": True})
    assert p.reset_after == 7200
    assert p.reset_on_success is True


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def test_get_quota_reset_state_path_uses_log_dir(log_dir):
    path = get_quota_reset_state_path("myjob", log_dir)
    assert path.parent == log_dir
    assert "myjob" in path.name


def test_load_quota_reset_state_returns_empty_when_no_file(log_dir):
    state = load_quota_reset_state("myjob", log_dir)
    assert state == {}


def test_save_and_load_roundtrip(log_dir):
    save_quota_reset_state("myjob", {"last_reset": 12345.0}, log_dir)
    state = load_quota_reset_state("myjob", log_dir)
    assert state["last_reset"] == pytest.approx(12345.0)


def test_record_reset_writes_timestamp(log_dir):
    before = time.time()
    record_reset("myjob", log_dir)
    state = load_quota_reset_state("myjob", log_dir)
    assert state["last_reset"] >= before


# ---------------------------------------------------------------------------
# should_reset
# ---------------------------------------------------------------------------

def test_should_reset_disabled_policy_returns_false(log_dir):
    p = QuotaResetPolicy()
    assert should_reset(p, "myjob", True, log_dir) is False


def test_should_reset_on_success_true_when_success(log_dir):
    p = QuotaResetPolicy(reset_on_success=True)
    assert should_reset(p, "myjob", True, log_dir) is True


def test_should_reset_on_success_false_when_failure(log_dir):
    p = QuotaResetPolicy(reset_on_success=True)
    assert should_reset(p, "myjob", False, log_dir) is False


def test_should_reset_after_elapsed(log_dir):
    p = QuotaResetPolicy(reset_after=1)
    # Write a last_reset far in the past
    save_quota_reset_state("myjob", {"last_reset": time.time() - 100}, log_dir)
    assert should_reset(p, "myjob", False, log_dir) is True


def test_should_reset_after_not_elapsed(log_dir):
    p = QuotaResetPolicy(reset_after=3600)
    save_quota_reset_state("myjob", {"last_reset": time.time()}, log_dir)
    assert should_reset(p, "myjob", False, log_dir) is False
