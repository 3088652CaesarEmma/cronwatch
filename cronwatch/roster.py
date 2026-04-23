"""Job roster: track which jobs are registered and their run eligibility status."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronwatch.log import get_log_dir


def get_roster_path(log_dir: Optional[str] = None) -> str:
    """Return the path to the roster state file."""
    base = log_dir or get_log_dir()
    return os.path.join(base, "roster.json")


@dataclass
class RosterEntry:
    name: str
    command: str
    enabled: bool = True
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def touch(self) -> None:
        """Update last_seen to now."""
        self.last_seen = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "command": self.command,
            "enabled": self.enabled,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RosterEntry":
        return cls(
            name=data["name"],
            command=data["command"],
            enabled=data.get("enabled", True),
            registered_at=data.get("registered_at", ""),
            last_seen=data.get("last_seen"),
            tags=data.get("tags", []),
        )


def load_roster(log_dir: Optional[str] = None) -> Dict[str, RosterEntry]:
    """Load roster from disk. Returns empty dict if no file exists."""
    path = get_roster_path(log_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as fh:
        raw = json.load(fh)
    return {name: RosterEntry.from_dict(entry) for name, entry in raw.items()}


def save_roster(roster: Dict[str, RosterEntry], log_dir: Optional[str] = None) -> None:
    """Persist roster to disk."""
    path = get_roster_path(log_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({name: entry.to_dict() for name, entry in roster.items()}, fh, indent=2)


def register_job(name: str, command: str, tags: Optional[List[str]] = None,
                 log_dir: Optional[str] = None) -> RosterEntry:
    """Register or refresh a job in the roster."""
    roster = load_roster(log_dir)
    if name in roster:
        entry = roster[name]
        entry.command = command
        entry.tags = tags or []
        entry.touch()
    else:
        entry = RosterEntry(name=name, command=command, tags=tags or [])
    roster[name] = entry
    save_roster(roster, log_dir)
    return entry


def deregister_job(name: str, log_dir: Optional[str] = None) -> bool:
    """Remove a job from the roster. Returns True if it existed."""
    roster = load_roster(log_dir)
    if name not in roster:
        return False
    del roster[name]
    save_roster(roster, log_dir)
    return True


def list_roster(log_dir: Optional[str] = None) -> List[RosterEntry]:
    """Return all roster entries sorted by name."""
    return sorted(load_roster(log_dir).values(), key=lambda e: e.name)
