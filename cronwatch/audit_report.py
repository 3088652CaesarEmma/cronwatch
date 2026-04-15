"""Generate human-readable audit reports from the audit trail."""
from __future__ import annotations

from collections import Counter
from typing import List, Optional

from cronwatch.audit import AuditEntry, read_audit


_HEADER = "{:<30} {:<12} {:<10} {:<10} {}".format(
    "JOB", "TRIGGERED", "EXIT", "DURATION", "FINISHED"
)
_SEP = "-" * 80


def _fmt_row(entry: AuditEntry) -> str:
    duration = f"{entry.duration_seconds:.2f}s"
    return "{:<30} {:<12} {:<10} {:<10} {}".format(
        entry.job_name[:29],
        entry.triggered_by[:11],
        str(entry.exit_code),
        duration,
        entry.finished_at[:19],
    )


def format_audit_table(entries: List[AuditEntry]) -> str:
    """Return a fixed-width table of audit entries."""
    if not entries:
        return "No audit entries found."
    rows = [_HEADER, _SEP]
    for e in entries:
        rows.append(_fmt_row(e))
    return "\n".join(rows)


def format_audit_summary(entries: List[AuditEntry]) -> str:
    """Return a short summary: total runs, success/failure counts, top jobs."""
    if not entries:
        return "No audit data."
    total = len(entries)
    failures = sum(1 for e in entries if e.exit_code != 0)
    successes = total - failures
    job_counts: Counter = Counter(e.job_name for e in entries)
    top = job_counts.most_common(3)
    top_str = ", ".join(f"{name}({n})" for name, n in top)
    lines = [
        f"Total runs : {total}",
        f"Succeeded  : {successes}",
        f"Failed     : {failures}",
        f"Top jobs   : {top_str}",
    ]
    return "\n".join(lines)


def print_audit_report(
    log_dir: str,
    limit: int = 50,
    job_name: Optional[str] = None,
) -> None:
    """Print a full audit report to stdout."""
    entries = read_audit(log_dir, limit=limit)
    if job_name:
        entries = [e for e in entries if e.job_name == job_name]
    print(format_audit_summary(entries))
    print()
    print(format_audit_table(entries))
