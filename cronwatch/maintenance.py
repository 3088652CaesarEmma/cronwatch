"""Maintenance window support: suppress job execution during scheduled downtime."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional


_TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')


def _parse_time(s: str) -> time:
    m = _TIME_RE.match(s.strip())
    if not m:
        raise ValueError(f"Invalid time format {s!r}. Expected HH:MM.")
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        raise ValueError(f"Time out of range: {s!r}")
    return time(hour, minute)


@dataclass
class MaintenanceWindow:
    start: time
    end: time
    days: List[int] = field(default_factory=list)  # 0=Mon … 6=Sun; empty = every day

    def __post_init__(self) -> None:
        for d in self.days:
            if d not in range(7):
                raise ValueError(f"Invalid day-of-week value: {d}. Must be 0-6.")

    def active_at(self, dt: Optional[datetime] = None) -> bool:
        dt = dt or datetime.now()
        if self.days and dt.weekday() not in self.days:
            return False
        current = dt.time().replace(second=0, microsecond=0)
        if self.start <= self.end:
            return self.start <= current < self.end
        # overnight window e.g. 22:00 – 06:00
        return current >= self.start or current < self.end

    @classmethod
    def from_str(cls, spec: str) -> "MaintenanceWindow":
        """Parse 'HH:MM-HH:MM' or 'HH:MM-HH:MM:Mon,Wed' style spec."""
        parts = spec.split(":")
        # Re-join to isolate time range vs optional day list
        # Format: HH:MM-HH:MM or HH:MM-HH:MM/Mon,Tue
        if "/" in spec:
            time_part, day_part = spec.split("/", 1)
        else:
            time_part, day_part = spec, ""

        if "-" not in time_part:
            raise ValueError(f"Maintenance window spec must contain '-': {spec!r}")

        start_str, end_str = time_part.split("-", 1)
        start = _parse_time(start_str)
        end = _parse_time(end_str)

        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        days: List[int] = []
        if day_part:
            for token in day_part.split(","):
                token = token.strip().lower()
                if token not in day_map:
                    raise ValueError(f"Unknown day abbreviation: {token!r}")
                days.append(day_map[token])

        return cls(start=start, end=end, days=days)


@dataclass
class MaintenancePolicy:
    windows: List[MaintenanceWindow] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.windows, list):
            raise TypeError("windows must be a list")

    def enabled(self) -> bool:
        return bool(self.windows)

    def is_active(self, dt: Optional[datetime] = None) -> bool:
        return any(w.active_at(dt) for w in self.windows)

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "MaintenancePolicy":
        if not cfg:
            return cls()
        specs = cfg.get("windows", [])
        if not isinstance(specs, list):
            raise TypeError("maintenance.windows must be a list of strings")
        windows = [MaintenanceWindow.from_str(s) for s in specs]
        return cls(windows=windows)
