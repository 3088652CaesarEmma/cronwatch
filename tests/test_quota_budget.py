"""Tests for cronwatch.quota_budget — QuotaBudgetGuard."""
from __future__ import annotations

import os
import pytest

from unittest.mock import MagicMock, patch

from cronwatch.quota_budget import QuotaBudgetGuard, BudgetExceededError
from cronwatch.quota import QuotaPolicy
from cronwatch.budget import BudgetPolicy


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _disabled_quota() -> QuotaPolicy:
    p = MagicMock(spec=QuotaPolicy)
    p.enabled = False
    return p


def _disabled_budget() -> BudgetPolicy:
    p = MagicMock(spec=BudgetPolicy)
    p.enabled = False
    return p


def _budget_under_limit(limit: float = 60.0, used: float = 10.0) -> BudgetPolicy:
    p = MagicMock(spec=BudgetPolicy)
    p.enabled = True
    p.max_seconds = limit
    p.get_used_seconds = MagicMock(return_value=used)
    return p


def _budget_over_limit(limit: float = 60.0, used: float = 70.0) -> BudgetPolicy:
    p = MagicMock(spec=BudgetPolicy)
    p.enabled = True
    p.max_seconds = limit
    p.get_used_seconds = MagicMock(return_value=used)
    return p


# ---------------------------------------------------------------------------
# BudgetExceededError
# ---------------------------------------------------------------------------

def test_budget_exceeded_error_message():
    err = BudgetExceededError("backup", 70.0, 60.0)
    assert "backup" in str(err)
    assert "70.0" in str(err)
    assert "60.0" in str(err)


def test_budget_exceeded_error_attributes():
    err = BudgetExceededError("backup", 70.0, 60.0)
    assert err.job_name == "backup"
    assert err.used == 70.0
    assert err.limit == 60.0


# ---------------------------------------------------------------------------
# QuotaBudgetGuard — both disabled
# ---------------------------------------------------------------------------

def test_guard_both_disabled_passes(log_dir):
    guard = QuotaBudgetGuard(
        job_name="myjob",
        quota_policy=_disabled_quota(),
        budget_policy=_disabled_budget(),
        log_dir=log_dir,
    )
    with guard:
        pass  # should not raise


# ---------------------------------------------------------------------------
# Budget enforcement
# ---------------------------------------------------------------------------

def test_guard_budget_under_limit_passes(log_dir):
    guard = QuotaBudgetGuard(
        job_name="myjob",
        quota_policy=_disabled_quota(),
        budget_policy=_budget_under_limit(),
        log_dir=log_dir,
    )
    with guard:
        pass


def test_guard_budget_over_limit_raises(log_dir):
    guard = QuotaBudgetGuard(
        job_name="myjob",
        quota_policy=_disabled_quota(),
        budget_policy=_budget_over_limit(),
        log_dir=log_dir,
    )
    with pytest.raises(BudgetExceededError):
        with guard:
            pass


def test_guard_budget_check_uses_job_name(log_dir):
    bp = _budget_under_limit()
    guard = QuotaBudgetGuard(
        job_name="special-job",
        quota_policy=_disabled_quota(),
        budget_policy=bp,
        log_dir=log_dir,
    )
    with guard:
        pass
    bp.get_used_seconds.assert_called_once_with("special-job", log_dir)


# ---------------------------------------------------------------------------
# Quota enforcement (via QuotaGuard)
# ---------------------------------------------------------------------------

def test_guard_quota_guard_entered_when_enabled(log_dir):
    quota = _disabled_quota()
    quota.enabled = True

    with patch("cronwatch.quota_budget.QuotaGuard") as MockQG:
        mock_instance = MagicMock()
        MockQG.return_value = mock_instance
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)

        guard = QuotaBudgetGuard(
            job_name="myjob",
            quota_policy=quota,
            budget_policy=_disabled_budget(),
            log_dir=log_dir,
        )
        with guard:
            pass

        mock_instance.__enter__.assert_called_once()
        mock_instance.__exit__.assert_called_once()


def test_guard_quota_guard_not_entered_when_disabled(log_dir):
    with patch("cronwatch.quota_budget.QuotaGuard") as MockQG:
        guard = QuotaBudgetGuard(
            job_name="myjob",
            quota_policy=_disabled_quota(),
            budget_policy=_disabled_budget(),
            log_dir=log_dir,
        )
        with guard:
            pass
        MockQG.assert_not_called()


# ---------------------------------------------------------------------------
# Exception propagation
# ---------------------------------------------------------------------------

def test_guard_does_not_suppress_exceptions(log_dir):
    guard = QuotaBudgetGuard(
        job_name="myjob",
        quota_policy=_disabled_quota(),
        budget_policy=_disabled_budget(),
        log_dir=log_dir,
    )
    with pytest.raises(RuntimeError, match="boom"):
        with guard:
            raise RuntimeError("boom")
