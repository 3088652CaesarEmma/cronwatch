"""Output formatting helpers for cronwatch CLI."""

from __future__ import annotations

from typing import List

from cronwatch.scheduler import CronEntry

_COL_SEP = "  "
_DISABLED_LABEL = "[disabled]"


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def format_job_table(jobs: List[CronEntry], max_cmd_width: int = 40) -> str:
    """Return a human-readable table of jobs."""
    if not jobs:
        return "No jobs found."

    headers = ("NAME", "SCHEDULE", "TAGS", "COMMAND", "STATUS")
    rows = []
    for j in jobs:
        tags = ",".join(j.tags or []) or "-"
        status = _DISABLED_LABEL if getattr(j, "disabled", False) else "enabled"
        rows.append((
            j.name,
            j.schedule,
            tags,
            _truncate(j.command, max_cmd_width),
            status,
        ))

    col_widths = [
        max(len(h), max(len(r[i]) for r in rows))
        for i, h in enumerate(headers)
    ]

    def fmt_row(row):
        return _COL_SEP.join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))

    sep = "-" * (sum(col_widths) + len(_COL_SEP) * (len(headers) - 1))
    lines = [fmt_row(headers), sep] + [fmt_row(r) for r in rows]
    return "\n".join(lines)


def format_job_names(jobs: List[CronEntry]) -> str:
    """Return a simple newline-separated list of job names."""
    if not jobs:
        return "No jobs found."
    return "\n".join(j.name for j in jobs)


def format_job_count(jobs: List[CronEntry]) -> str:
    """Return a summary count string."""
    total = len(jobs)
    enabled = sum(1 for j in jobs if not getattr(j, "disabled", False))
    disabled = total - enabled
    return f"Total: {total}  Enabled: {enabled}  Disabled: {disabled}"
