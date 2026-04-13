"""Scheduler module for parsing and evaluating cron expressions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CronEntry:
    """Represents a single cron job entry."""
    name: str
    command: str
    schedule: str
    enabled: bool = True
    timeout: Optional[int] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            raise ValueError("CronEntry name cannot be empty")
        if not self.command:
            raise ValueError("CronEntry command cannot be empty")
        if not self.schedule:
            raise ValueError("CronEntry schedule cannot be empty")


def parse_cron_field(field_str: str, min_val: int, max_val: int) -> List[int]:
    """Parse a single cron field and return list of matching values."""
    values = []

    if field_str == "*":
        return list(range(min_val, max_val + 1))

    for part in field_str.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
            start = min_val if base == "*" else int(base)
            values.extend(range(start, max_val + 1, step))
        elif "-" in part:
            start, end = part.split("-", 1)
            values.extend(range(int(start), int(end) + 1))
        else:
            values.append(int(part))

    return sorted(set(v for v in values if min_val <= v <= max_val))


def is_due(schedule: str, dt: Optional[datetime] = None) -> bool:
    """Check if a cron schedule is due at the given datetime."""
    if dt is None:
        dt = datetime.now()

    parts = schedule.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron schedule: '{schedule}'. Expected 5 fields.")

    minute_field, hour_field, dom_field, month_field, dow_field = parts

    minutes = parse_cron_field(minute_field, 0, 59)
    hours = parse_cron_field(hour_field, 0, 23)
    doms = parse_cron_field(dom_field, 1, 31)
    months = parse_cron_field(month_field, 1, 12)
    dows = parse_cron_field(dow_field, 0, 6)

    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in doms
        and dt.month in months
        and dt.weekday() in [d % 7 for d in dows]
    )


def get_due_jobs(entries: List[CronEntry], dt: Optional[datetime] = None) -> List[CronEntry]:
    """Return list of enabled cron entries that are due at the given time."""
    due = []
    for entry in entries:
        if not entry.enabled:
            continue
        try:
            if is_due(entry.schedule, dt):
                due.append(entry)
        except ValueError as e:
            logger.warning("Skipping job '%s': %s", entry.name, e)
    return due
