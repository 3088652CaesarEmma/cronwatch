"""Audit trail: record every job execution attempt with metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from cronwatch.runner import JobResult


@dataclass
class AuditEntry:
    job_name: str
    command: str
    started_at: str
    finished_at: str
    exit_code: int
    duration_seconds: float
    triggered_by: str = "manual"  # manual | scheduler | cli
    tags: List[str] = None
    note: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def get_audit_path(log_dir: str) -> Path:
    """Return the path to the audit log JSONL file."""
    return Path(log_dir) / "audit.jsonl"


def record_audit(
    result: JobResult,
    log_dir: str,
    job_name: str = "",
    triggered_by: str = "manual",
    tags: Optional[List[str]] = None,
    note: Optional[str] = None,
) -> AuditEntry:
    """Append an audit entry for *result* and return it."""
    now_iso = datetime.now(timezone.utc).isoformat()
    entry = AuditEntry(
        job_name=job_name or result.command.split()[0],
        command=result.command,
        started_at=getattr(result, "started_at", now_iso),
        finished_at=getattr(result, "finished_at", now_iso),
        exit_code=result.exit_code,
        duration_seconds=round(getattr(result, "duration", 0.0), 3),
        triggered_by=triggered_by,
        tags=tags or [],
        note=note,
    )
    path = get_audit_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
    return entry


def read_audit(log_dir: str, limit: int = 100) -> List[AuditEntry]:
    """Read the most recent *limit* audit entries (oldest-first slice)."""
    path = get_audit_path(log_dir)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    recent = lines[-limit:]
    entries = []
    for line in recent:
        try:
            data = json.loads(line)
            entries.append(AuditEntry(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return entries
