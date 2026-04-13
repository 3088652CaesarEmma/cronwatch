"""Structured logging utilities for cronwatch job execution."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from cronwatch.runner import JobResult

LOG_DIR_ENV = "CRONWATCH_LOG_DIR"
DEFAULT_LOG_DIR = "/var/log/cronwatch"


def get_log_dir() -> Path:
    """Return the log directory, preferring the environment variable."""
    return Path(os.environ.get(LOG_DIR_ENV, DEFAULT_LOG_DIR))


def _result_to_dict(result: JobResult) -> dict:
    return {
        "job": result.job_name,
        "command": result.command,
        "exit_code": result.exit_code,
        "success": result.exit_code == 0,
        "duration_seconds": round(result.duration, 3),
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def log_result_json(result: JobResult, log_dir: Path | None = None) -> Path:
    """Append a JSON log entry for *result* to a per-job log file.

    Returns the path of the log file written.
    """
    directory = log_dir or get_log_dir()
    directory.mkdir(parents=True, exist_ok=True)

    safe_name = result.job_name.replace(" ", "_").replace("/", "_")
    log_file = directory / f"{safe_name}.log"

    entry = _result_to_dict(result)
    entry["logged_at"] = datetime.utcnow().isoformat()

    with log_file.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    return log_file


def setup_stderr_logger(name: str = "cronwatch", level: int = logging.INFO) -> logging.Logger:
    """Return a simple stderr logger for cronwatch internals."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def read_job_log(job_name: str, log_dir: Path | None = None) -> list[dict]:
    """Read all log entries for a job and return them as a list of dicts."""
    directory = log_dir or get_log_dir()
    safe_name = job_name.replace(" ", "_").replace("/", "_")
    log_file = directory / f"{safe_name}.log"

    if not log_file.exists():
        return []

    entries = []
    with log_file.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def tail_job_log(job_name: str, n: int = 10, log_dir: Path | None = None) -> list[dict]:
    """Return the last *n* log entries for a job.

    Useful for quickly inspecting recent runs without loading the entire log.
    Returns an empty list if no log file exists for the job.
    """
    return read_job_log(job_name, log_dir=log_dir)[-n:]


def list_logged_jobs(log_dir: Path | None = None) -> list[str]:
    """Return a sorted list of job names that have log files in *log_dir*.

    Job names are reconstructed from the log filenames by reversing the
    sanitisation applied in :func:`log_result_json` (underscores are left
    as-is since the original spaces and slashes are indistinguishable after
    sanitisation, but the stem is returned as-is for transparency).

    Returns an empty list if the log directory does not exist.
    """
    directory = log_dir or get_log_dir()
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.log"))
