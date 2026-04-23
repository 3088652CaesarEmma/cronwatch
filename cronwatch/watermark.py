"""High-watermark tracking: record and compare peak resource usage per job."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from cronwatch.log import get_log_dir
from cronwatch.runner import JobResult


@dataclass
class WatermarkPolicy:
    """Policy controlling whether high-watermark tracking is enabled."""

    enabled: bool = False
    track_duration: bool = True
    track_output_bytes: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
        if not isinstance(self.track_duration, bool):
            raise TypeError("track_duration must be a bool")
        if not isinstance(self.track_output_bytes, bool):
            raise TypeError("track_output_bytes must be a bool")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "WatermarkPolicy":
        if not cfg:
            return cls()
        return cls(
            enabled=bool(cfg.get("enabled", False)),
            track_duration=bool(cfg.get("track_duration", True)),
            track_output_bytes=bool(cfg.get("track_output_bytes", True)),
        )


def get_watermark_path(job_name: str, log_dir: Optional[str] = None) -> str:
    base = log_dir or get_log_dir()
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return os.path.join(base, f"{safe}.watermark.json")


def load_watermarks(job_name: str, log_dir: Optional[str] = None) -> Dict[str, float]:
    path = get_watermark_path(job_name, log_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as fh:
        return json.load(fh)


def save_watermarks(job_name: str, marks: Dict[str, float], log_dir: Optional[str] = None) -> None:
    path = get_watermark_path(job_name, log_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(marks, fh)


def update_watermarks(
    result: JobResult,
    policy: WatermarkPolicy,
    log_dir: Optional[str] = None,
) -> Dict[str, float]:
    """Update stored watermarks with values from *result*; return updated dict."""
    if not policy.enabled:
        return {}
    marks = load_watermarks(result.command, log_dir)
    if policy.track_duration and result.duration is not None:
        prev = marks.get("duration", None)
        if prev is None or result.duration > prev:
            marks["duration"] = result.duration
    if policy.track_output_bytes:
        combined = len((result.stdout or "").encode()) + len((result.stderr or "").encode())
        prev_bytes = marks.get("output_bytes", None)
        if prev_bytes is None or combined > prev_bytes:
            marks["output_bytes"] = float(combined)
    save_watermarks(result.command, marks, log_dir)
    return marks
