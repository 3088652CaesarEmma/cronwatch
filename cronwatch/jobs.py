"""Load and filter job definitions from config."""

from __future__ import annotations

from typing import Any

from cronwatch.scheduler import CronEntry
from cronwatch.retry import RetryPolicy, policy_from_config


def _build_entry(raw: dict[str, Any], defaults: dict[str, Any]) -> CronEntry | None:
    """Return a CronEntry built from *raw*, merged with *defaults*, or None if invalid."""
    try:
        merged = {**defaults, **raw}
        return CronEntry(
            name=merged["name"],
            command=merged["command"],
            schedule=merged.get("schedule", "* * * * *"),
            enabled=merged.get("enabled", True),
            tags=merged.get("tags", []),
            timeout=merged.get("timeout"),
            retry_policy=policy_from_config(merged),
        )
    except (KeyError, ValueError, TypeError):
        return None


def load_jobs_from_config(config: Any) -> list[CronEntry]:
    """Load all enabled job entries from a CronwatchConfig object."""
    raw_jobs: list[dict] = getattr(config, "jobs", []) or []
    defaults: dict = getattr(config, "defaults", {}) or {}
    entries = []
    for raw in raw_jobs:
        entry = _build_entry(raw, defaults)
        if entry is not None and entry.enabled:
            entries.append(entry)
    return entries


def load_jobs_from_file(path: str) -> list[CronEntry]:
    """Load job definitions directly from a YAML file path."""
    import yaml

    with open(path) as fh:
        data = yaml.safe_load(fh) or {}

    defaults = data.get("defaults", {})
    raw_jobs = data.get("jobs", [])
    entries = []
    for raw in raw_jobs:
        entry = _build_entry(raw, defaults)
        if entry is not None and entry.enabled:
            entries.append(entry)
    return entries


def find_job_by_name(jobs: list[CronEntry], name: str) -> CronEntry | None:
    """Return the first job whose name matches *name* (case-sensitive)."""
    return next((j for j in jobs if j.name == name), None)


def filter_jobs_by_tag(jobs: list[CronEntry], tag: str) -> list[CronEntry]:
    """Return jobs that carry *tag* in their tags list."""
    return [j for j in jobs if tag in (j.tags or [])]
