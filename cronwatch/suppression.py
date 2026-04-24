"""Suppression policy: silence notifications for a job during a defined time window."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


def _parse_time(value: str) -> time:
    """Parse HH:MM into a time object."""
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        raise ValueError(f"Invalid time format {value!r}, expected HH:MM")


@dataclass
class SuppressionPolicy:
    """Defines a window during which job notifications are suppressed."""

    start: Optional[time] = None
    end: Optional[time] = None
    comment: str = ""

    def __post_init__(self) -> None:
        if (self.start is None) != (self.end is None):
            raise ValueError("Both 'start' and 'end' must be set together")

    @property
    def enabled(self) -> bool:
        return self.start is not None and self.end is not None

    def is_suppressed(self, at: Optional[datetime] = None) -> bool:
        """Return True if *at* (default: now) falls within the suppression window."""
        if not self.enabled:
            return False
        now = (at or datetime.now()).time()
        if self.start <= self.end:  # type: ignore[operator]
            return self.start <= now <= self.end  # type: ignore[operator]
        # Overnight window e.g. 22:00 – 06:00
        return now >= self.start or now <= self.end  # type: ignore[operator]

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SuppressionPolicy":
        if not cfg:
            return cls()
        start = _parse_time(cfg["start"]) if "start" in cfg else None
        end = _parse_time(cfg["end"]) if "end" in cfg else None
        comment = cfg.get("comment", "")
        return cls(start=start, end=end, comment=comment)


def get_suppression_state_path(log_dir: Path, job_name: str) -> Path:
    safe = job_name.replace(" ", "_").replace("/", "_")
    return log_dir / "suppression" / f"{safe}.json"


def load_suppression_overrides(log_dir: Path) -> dict:
    """Load manually-set suppression overrides (job_name -> ISO end datetime)."""
    path = log_dir / "suppression" / "overrides.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_suppression_overrides(log_dir: Path, overrides: dict) -> None:
    path = log_dir / "suppression" / "overrides.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overrides, indent=2))


def suppress_until(log_dir: Path, job_name: str, until: datetime) -> None:
    """Manually suppress notifications for *job_name* until *until*."""
    overrides = load_suppression_overrides(log_dir)
    overrides[job_name] = until.isoformat()
    save_suppression_overrides(log_dir, overrides)


def is_manually_suppressed(log_dir: Path, job_name: str, at: Optional[datetime] = None) -> bool:
    """Return True if a manual override is active for *job_name* at *at*."""
    overrides = load_suppression_overrides(log_dir)
    if job_name not in overrides:
        return False
    until = datetime.fromisoformat(overrides[job_name])
    return (at or datetime.now()) < until
