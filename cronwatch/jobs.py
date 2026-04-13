"""Job loading and management utilities."""

from typing import List, Optional
import logging
import yaml

from cronwatch.scheduler import CronEntry

logger = logging.getLogger(__name__)


def load_jobs_from_config(config_data: dict) -> List[CronEntry]:
    """Load CronEntry objects from a parsed config dictionary."""
    raw_jobs = config_data.get("jobs", [])
    entries = []

    for raw in raw_jobs:
        try:
            entry = CronEntry(
                name=raw["name"],
                command=raw["command"],
                schedule=raw["schedule"],
                enabled=raw.get("enabled", True),
                timeout=raw.get("timeout", None),
                tags=raw.get("tags", []),
            )
            entries.append(entry)
        except (KeyError, ValueError) as e:
            logger.warning("Skipping invalid job entry %r: %s", raw, e)

    logger.debug("Loaded %d job(s) from config", len(entries))
    return entries


def load_jobs_from_file(path: str) -> List[CronEntry]:
    """Load CronEntry objects from a YAML file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    return load_jobs_from_config(data)


def find_job_by_name(entries: List[CronEntry], name: str) -> Optional[CronEntry]:
    """Find a CronEntry by its name."""
    for entry in entries:
        if entry.name == name:
            return entry
    return None


def filter_jobs_by_tag(entries: List[CronEntry], tag: str) -> List[CronEntry]:
    """Return only entries that have the given tag."""
    return [e for e in entries if tag in e.tags]
