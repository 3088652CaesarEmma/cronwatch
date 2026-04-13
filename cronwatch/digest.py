"""Digest: periodic summary reports aggregating multiple job results."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from cronwatch.history import read_history
from cronwatch.summary import RunSummary


@dataclass
class DigestPolicy:
    enabled: bool = False
    interval_hours: int = 24
    only_on_failure: bool = False

    def __post_init__(self) -> None:
        if self.interval_hours <= 0:
            raise ValueError("interval_hours must be a positive integer")

    @classmethod
    def from_config(cls, cfg: dict) -> "DigestPolicy":
        digest_cfg = cfg.get("digest", {})
        return cls(
            enabled=digest_cfg.get("enabled", False),
            interval_hours=digest_cfg.get("interval_hours", 24),
            only_on_failure=digest_cfg.get("only_on_failure", False),
        )


def get_digest_state_path(log_dir: str) -> str:
    return os.path.join(log_dir, "digest_state.json")


def load_digest_state(log_dir: str) -> dict:
    path = get_digest_state_path(log_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_digest_state(log_dir: str, state: dict) -> None:
    path = get_digest_state_path(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f)


def is_digest_due(policy: DigestPolicy, log_dir: str) -> bool:
    if not policy.enabled:
        return False
    state = load_digest_state(log_dir)
    last_sent = state.get("last_sent")
    if last_sent is None:
        return True
    last_dt = datetime.fromisoformat(last_sent)
    return datetime.utcnow() - last_dt >= timedelta(hours=policy.interval_hours)


def build_digest(job_names: List[str], log_dir: str, policy: DigestPolicy) -> Optional[RunSummary]:
    summary = RunSummary()
    for name in job_names:
        for result in read_history(name, log_dir=log_dir):
            summary.add(result)
    if policy.only_on_failure and summary.failed == 0:
        return None
    return summary


def mark_digest_sent(log_dir: str) -> None:
    state = load_digest_state(log_dir)
    state["last_sent"] = datetime.utcnow().isoformat()
    save_digest_state(log_dir, state)
