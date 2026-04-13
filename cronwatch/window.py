"""Time window policy — restrict job execution to allowed time ranges."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional

_TIME_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')


def _parse_time(value: str) -> time:
    m = _TIME_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid time format {value!r}; expected HH:MM (24-hour)")
    return time(int(m.group(1)), int(m.group(2)))


@dataclass
class TimeWindow:
    start: time
    end: time

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"Window start {self.start} must be before end {self.end}"
            )

    def contains(self, t: time) -> bool:
        """Return True if *t* falls within [start, end)."""
        return self.start <= t < self.end

    @classmethod
    def from_str(cls, value: str) -> "TimeWindow":
        """Parse 'HH:MM-HH:MM' into a TimeWindow."""
        if '-' not in value:
            raise ValueError(f"Expected 'HH:MM-HH:MM', got {value!r}")
        raw_start, raw_end = value.split('-', 1)
        return cls(start=_parse_time(raw_start), end=_parse_time(raw_end))


@dataclass
class WindowPolicy:
    windows: List[TimeWindow] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.windows, list):
            raise TypeError("windows must be a list")

    @property
    def enabled(self) -> bool:
        return bool(self.windows)

    def is_allowed(self, dt: Optional[datetime] = None) -> bool:
        """Return True when *dt* (default: now) falls inside any window."""
        if not self.enabled:
            return True
        t = (dt or datetime.now()).time()
        return any(w.contains(t) for w in self.windows)

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "WindowPolicy":
        if not cfg:
            return cls()
        raw = cfg.get("windows", [])
        if not isinstance(raw, list):
            raise TypeError("window.windows must be a list of 'HH:MM-HH:MM' strings")
        return cls(windows=[TimeWindow.from_str(s) for s in raw])
