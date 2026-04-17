"""Tests for cronwatch.expiry and cronwatch.expiry_guard."""
from datetime import date
import pytest

from cronwatch.expiry import ExpiryPolicy, JobExpiredError
from cronwatch.expiry_guard import ExpiryGuard


def test_expiry_policy_defaults():
    p = ExpiryPolicy()
    assert p.expires_on is None
    assert not p.enabled


def test_expiry_policy_with_date():
    d = date(2030, 1, 1)
    p = ExpiryPolicy(expires_on=d)
    assert p.enabled
    assert p.expires_on == d


def test_expiry_policy_invalid_type_raises():
    with pytest.raises(TypeError):
        ExpiryPolicy(expires_on="2030-01-01")


def test_is_expired_before_expiry():
    p = ExpiryPolicy(expires_on=date(2099, 12, 31))
    assert not p.is_expired(today=date(2024, 1, 1))


def test_is_expired_on_expiry_date():
    d = date(2024, 6, 1)
    p = ExpiryPolicy(expires_on=d)
    assert not p.is_expired(today=d)


def test_is_expired_after_expiry():
    p = ExpiryPolicy(expires_on=date(2020, 1, 1))
    assert p.is_expired(today=date(2024, 6, 1))


def test_is_expired_disabled_policy():
    p = ExpiryPolicy()
    assert not p.is_expired(today=date(2000, 1, 1))


def test_from_config_none_returns_defaults():
    p = ExpiryPolicy.from_config(None)
    assert not p.enabled


def test_from_config_empty_dict_returns_defaults():
    p = ExpiryPolicy.from_config({})
    assert not p.enabled


def test_from_config_string_date():
    p = ExpiryPolicy.from_config({"expires_on": "2030-06-15"})
    assert p.expires_on == date(2030, 6, 15)


def test_from_config_date_object():
    d = date(2030, 6, 15)
    p = ExpiryPolicy.from_config({"expires_on": d})
    assert p.expires_on == d


def test_job_expired_error_message():
    err = JobExpiredError("my-job", date(2020, 1, 1))
    assert "my-job" in str(err)
    assert "2020-01-01" in str(err)


def test_guard_allows_when_not_expired():
    policy = ExpiryPolicy(expires_on=date(2099, 1, 1))
    with ExpiryGuard(policy, "job", today=date(2024, 1, 1)):
        pass  # should not raise


def test_guard_raises_when_expired():
    policy = ExpiryPolicy(expires_on=date(2020, 1, 1))
    with pytest.raises(JobExpiredError) as exc_info:
        with ExpiryGuard(policy, "old-job", today=date(2024, 1, 1)):
            pass
    assert exc_info.value.job_name == "old-job"


def test_guard_disabled_policy_always_passes():
    policy = ExpiryPolicy()
    with ExpiryGuard(policy, "job", today=date(1990, 1, 1)):
        pass
