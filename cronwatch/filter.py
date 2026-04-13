"""Job filtering utilities for cronwatch."""

from __future__ import annotations

from typing import List, Optional

from cronwatch.scheduler import CronEntry


def filter_by_name(jobs: List[CronEntry], name: str) -> Optional[CronEntry]:
    """Return the first job whose name matches exactly, or None."""
    for job in jobs:
        if job.name == name:
            return job
    return None


def filter_by_tag(jobs: List[CronEntry], tag: str) -> List[CronEntry]:
    """Return all jobs that carry the given tag."""
    return [j for j in jobs if tag in (j.tags or [])]


def filter_by_tags_any(jobs: List[CronEntry], tags: List[str]) -> List[CronEntry]:
    """Return jobs that have at least one of the given tags."""
    tag_set = set(tags)
    return [j for j in jobs if tag_set.intersection(j.tags or [])]


def filter_by_tags_all(jobs: List[CronEntry], tags: List[str]) -> List[CronEntry]:
    """Return jobs that have ALL of the given tags."""
    tag_set = set(tags)
    return [j for j in jobs if tag_set.issubset(j.tags or [])]


def filter_enabled(jobs: List[CronEntry]) -> List[CronEntry]:
    """Return only enabled (non-disabled) jobs."""
    return [j for j in jobs if not getattr(j, 'disabled', False)]


def filter_disabled(jobs: List[CronEntry]) -> List[CronEntry]:
    """Return only disabled jobs."""
    return [j for j in jobs if getattr(j, 'disabled', False)]


def search_jobs(jobs: List[CronEntry], query: str) -> List[CronEntry]:
    """Return jobs whose name or command contains the query string (case-insensitive)."""
    q = query.lower()
    return [
        j for j in jobs
        if q in j.name.lower() or q in j.command.lower()
    ]
