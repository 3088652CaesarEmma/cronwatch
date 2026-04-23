"""Snapshot policy: capture and compare job output hashes to detect unexpected changes."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.log import get_log_dir


@dataclass
class SnapshotPolicy:
    enabled: bool = False
    alert_on_change: bool = True
    store_output: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.alert_on_change, bool):
            raise TypeError("alert_on_change must be a bool")
        if not isinstance(self.store_output, bool):
            raise TypeError("store_output must be a bool")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "SnapshotPolicy":
        if not cfg:
            return cls()
        return cls(
            enabled=bool(cfg.get("enabled", False)),
            alert_on_change=bool(cfg.get("alert_on_change", True)),
            store_output=bool(cfg.get("store_output", False)),
        )


def get_snapshot_path(job_name: str) -> Path:
    return get_log_dir() / "snapshots" / f"{job_name}.json"


def _hash_output(output: str) -> str:
    return hashlib.sha256(output.encode()).hexdigest()


def load_snapshot(job_name: str) -> Optional[dict]:
    path = get_snapshot_path(job_name)
    if not path.exists():
        return None
    with path.open() as fh:
        return json.load(fh)


def save_snapshot(job_name: str, output: str) -> None:
    path = get_snapshot_path(job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"hash": _hash_output(output), "output": output}
    with path.open("w") as fh:
        json.dump(data, fh)


def output_changed(job_name: str, current_output: str) -> bool:
    """Return True if output differs from the stored snapshot (or no snapshot exists)."""
    snapshot = load_snapshot(job_name)
    if snapshot is None:
        return True
    return snapshot["hash"] != _hash_output(current_output)
