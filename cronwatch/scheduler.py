"""Cron scheduling helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class CronEntry:
    """Represents a single scheduled cron job."""

    name: str
    command: str
    schedule: str = "* * * * *"
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_policy: Any = None  # RetryPolicy — kept as Any to avoid circular import

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("CronEntry name must not be empty")
        if not self.command:
            raise ValueError("CronEntry command must not be empty")


def parse_cron_field(field_str: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field string into a set of matching integers."""
    if field_str == "*":
        return set(range(min_val, max_val + 1))

    values: set[int] = set()
    for part in field_str.split(","):
        if "/" in part:
            range_part, step_str = part.split("/", 1)
            step = int(step_str)
            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                start, end = (int(x) for x in range_part.split("-", 1))
            else:
                start = end = int(range_part)
            values.update(range(start, end + 1, step))
        elif "-" in part:
            start, end = (int(x) for x in part.split("-", 1))
            values.update(range(start, end + 1))
        else:
            values.add(int(part))
    return values


def is_due(entry: CronEntry, at: datetime) -> bool:
    """Return True if *entry* is scheduled to run at *at*."""
    if not entry.enabled:
        return False

    parts = entry.schedule.split()
    if len(parts) != 5:
        return False

    minute_f, hour_f, dom_f, month_f, dow_f = parts

    checks = [
        (minute_f, 0, 59, at.minute),
        (hour_f, 0, 23, at.hour),
        (dom_f, 1, 31, at.day),
        (month_f, 1, 12, at.month),
        (dow_f, 0, 6, at.weekday()),  # Monday=0 … Sunday=6
    ]

    for field_str, lo, hi, value in checks:
        try:
            if value not in parse_cron_field(field_str, lo, hi):
                return False
        except (ValueError, IndexError):
            return False

    return True


def get_due_jobs(entries: list[CronEntry], at: datetime | None = None) -> list[CronEntry]:
    """Return all entries that are due at *at* (defaults to now)."""
    if at is None:
        at = datetime.now()
    return [e for e in entries if is_due(e, at)]
