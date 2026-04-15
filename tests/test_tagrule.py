"""Tests for cronwatch.tagrule and cronwatch.tagrule_guard."""

import pytest

from cronwatch.tagrule import TagRulePolicy
from cronwatch.tagrule_guard import TagRuleGuard, TagRuleViolationError


# ---------------------------------------------------------------------------
# TagRulePolicy construction
# ---------------------------------------------------------------------------

def test_tagrule_policy_defaults():
    p = TagRulePolicy()
    assert p.require_any == []
    assert p.require_all == []
    assert p.exclude == []


def test_tagrule_policy_invalid_require_any_type_raises():
    with pytest.raises(TypeError):
        TagRulePolicy(require_any="production")


def test_tagrule_policy_empty_string_entry_raises():
    with pytest.raises(ValueError):
        TagRulePolicy(require_all=[""])


def test_tagrule_policy_strips_whitespace():
    p = TagRulePolicy(require_any=[" prod ", " staging "])
    assert p.require_any == ["prod", "staging"]


def test_tagrule_policy_enabled_when_rules_present():
    p = TagRulePolicy(require_any=["prod"])
    assert p.enabled() is True


def test_tagrule_policy_disabled_when_empty():
    p = TagRulePolicy()
    assert p.enabled() is False


# ---------------------------------------------------------------------------
# TagRulePolicy.matches
# ---------------------------------------------------------------------------

def test_matches_require_any_satisfied():
    p = TagRulePolicy(require_any=["prod", "staging"])
    assert p.matches(["prod", "db"]) is True


def test_matches_require_any_not_satisfied():
    p = TagRulePolicy(require_any=["prod"])
    assert p.matches(["staging", "db"]) is False


def test_matches_require_all_satisfied():
    p = TagRulePolicy(require_all=["prod", "critical"])
    assert p.matches(["prod", "critical", "db"]) is True


def test_matches_require_all_not_satisfied():
    p = TagRulePolicy(require_all=["prod", "critical"])
    assert p.matches(["prod"]) is False


def test_matches_exclude_blocks():
    p = TagRulePolicy(exclude=["disabled"])
    assert p.matches(["prod", "disabled"]) is False


def test_matches_exclude_allows_when_absent():
    p = TagRulePolicy(exclude=["disabled"])
    assert p.matches(["prod"]) is True


def test_matches_combined_rules():
    p = TagRulePolicy(require_any=["prod"], exclude=["skip"])
    assert p.matches(["prod"]) is True
    assert p.matches(["prod", "skip"]) is False
    assert p.matches(["staging"]) is False


def test_from_config_none_returns_defaults():
    p = TagRulePolicy.from_config(None)
    assert p.enabled() is False


def test_from_config_dict():
    p = TagRulePolicy.from_config({"require_any": ["prod"], "exclude": ["disabled"]})
    assert p.require_any == ["prod"]
    assert p.exclude == ["disabled"]


# ---------------------------------------------------------------------------
# TagRuleGuard
# ---------------------------------------------------------------------------

def test_guard_passes_when_tags_match():
    p = TagRulePolicy(require_any=["prod"])
    with TagRuleGuard("myjob", ["prod"], p):
        pass  # should not raise


def test_guard_raises_when_tags_do_not_match():
    p = TagRulePolicy(require_any=["prod"])
    with pytest.raises(TagRuleViolationError) as exc_info:
        with TagRuleGuard("myjob", ["staging"], p):
            pass
    assert "myjob" in str(exc_info.value)


def test_guard_disabled_policy_always_passes():
    p = TagRulePolicy()
    with TagRuleGuard("myjob", [], p):
        pass  # no rules → always passes


def test_violation_error_contains_job_name():
    p = TagRulePolicy(require_all=["critical"])
    err = TagRuleViolationError("backup", ["prod"], p)
    assert "backup" in str(err)


def test_violation_error_contains_tags():
    p = TagRulePolicy(require_all=["critical"])
    err = TagRuleViolationError("backup", ["prod"], p)
    assert "prod" in str(err)
