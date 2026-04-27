"""Tests for cronwatch.quota_alert."""
import time
import json
from pathlib import Path

import pytest

from cronwatch.quota_alert import QuotaAlertPolicy, check_quota_alert
from cronwatch.quota import QuotaPolicy


# ---------------------------------------------------------------------------
# QuotaAlertPolicy unit tests
# ---------------------------------------------------------------------------

def test_quota_alert_policy_defaults():
    p = QuotaAlertPolicy()
    assert p.threshold == 0.0
    assert p.notify_once is True
    assert p.enabled is False


def test_quota_alert_policy_enabled_when_threshold_nonzero():
    p = QuotaAlertPolicy(threshold=0.8)
    assert p.enabled is True


def test_quota_alert_policy_threshold_zero_disables():
    p = QuotaAlertPolicy(threshold=0.0)
    assert p.enabled is False


def test_quota_alert_policy_invalid_threshold_type_raises():
    with pytest.raises(TypeError):
        QuotaAlertPolicy(threshold="high")


def test_quota_alert_policy_threshold_above_one_raises():
    with pytest.raises(ValueError):
        QuotaAlertPolicy(threshold=1.5)


def test_quota_alert_policy_threshold_negative_raises():
    with pytest.raises(ValueError):
        QuotaAlertPolicy(threshold=-0.1)


def test_quota_alert_policy_invalid_notify_once_raises():
    with pytest.raises(TypeError):
        QuotaAlertPolicy(threshold=0.5, notify_once="yes")


def test_from_config_none_returns_defaults():
    p = QuotaAlertPolicy.from_config(None)
    assert p.threshold == 0.0
    assert p.notify_once is True


def test_from_config_sets_fields():
    p = QuotaAlertPolicy.from_config({"threshold": 0.75, "notify_once": False})
    assert p.threshold == 0.75
    assert p.notify_once is False


# ---------------------------------------------------------------------------
# check_quota_alert integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _seed_runs(job_name: str, log_dir: str, count: int, window: int = 3600):
    """Write fake quota state entries."""
    from cronwatch.quota import get_quota_state_path
    path = Path(get_quota_state_path(job_name, log_dir))
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    entries = [now - i for i in range(count)]
    path.write_text(json.dumps(entries))


def test_check_quota_alert_disabled_policy_returns_none(log_dir):
    quota = QuotaPolicy(max_runs=10, window_seconds=3600)
    alert = QuotaAlertPolicy()  # disabled
    result = check_quota_alert("myjob", quota, alert, log_dir)
    assert result is None


def test_check_quota_alert_below_threshold_returns_none(log_dir):
    _seed_runs("myjob", log_dir, count=3)
    quota = QuotaPolicy(max_runs=10, window_seconds=3600)
    alert = QuotaAlertPolicy(threshold=0.8)
    result = check_quota_alert("myjob", quota, alert, log_dir)
    assert result is None


def test_check_quota_alert_at_threshold_returns_message(log_dir):
    _seed_runs("myjob", log_dir, count=8)
    quota = QuotaPolicy(max_runs=10, window_seconds=3600)
    alert = QuotaAlertPolicy(threshold=0.8)
    result = check_quota_alert("myjob", quota, alert, log_dir)
    assert result is not None
    assert "myjob" in result
    assert "8/10" in result


def test_check_quota_alert_message_contains_percentage(log_dir):
    _seed_runs("myjob", log_dir, count=9)
    quota = QuotaPolicy(max_runs=10, window_seconds=3600)
    alert = QuotaAlertPolicy(threshold=0.5)
    result = check_quota_alert("myjob", quota, alert, log_dir)
    assert "90%" in result
