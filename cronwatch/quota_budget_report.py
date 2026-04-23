"""quota_budget_report.py — Tabular report combining quota and budget state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from cronwatch.quota import QuotaPolicy
from cronwatch.budget import BudgetPolicy

_COL_WIDTHS = (24, 12, 12, 12, 12)
_HEADERS = ("Job", "Quota Used", "Quota Max", "Budget Used", "Budget Max")


@dataclass
class QuotaBudgetRow:
    job_name: str
    quota_used: int
    quota_max: int
    budget_used: float
    budget_max: float

    @property
    def quota_ok(self) -> bool:
        return self.quota_max == 0 or self.quota_used < self.quota_max

    @property
    def budget_ok(self) -> bool:
        return self.budget_max == 0.0 or self.budget_used < self.budget_max


def build_report_rows(
    job_names: Sequence[str],
    job_configs: dict,
    log_dir: str,
) -> List[QuotaBudgetRow]:
    """Build one :class:`QuotaBudgetRow` per job name."""
    rows: List[QuotaBudgetRow] = []
    for name in job_names:
        cfg = job_configs.get(name, {})
        qp = QuotaPolicy.from_config(cfg.get("quota"))
        bp = BudgetPolicy.from_config(cfg.get("budget"))

        quota_used = qp.get_run_count(name, log_dir) if qp.enabled else 0
        quota_max = qp.max_runs if qp.enabled else 0
        budget_used = bp.get_used_seconds(name, log_dir) if bp.enabled else 0.0
        budget_max = bp.max_seconds if bp.enabled else 0.0

        rows.append(
            QuotaBudgetRow(
                job_name=name,
                quota_used=quota_used,
                quota_max=quota_max,
                budget_used=budget_used,
                budget_max=budget_max,
            )
        )
    return rows


def _fmt(value: str, width: int) -> str:
    return value[:width].ljust(width)


def format_report_table(rows: List[QuotaBudgetRow]) -> str:
    """Render *rows* as a plain-text table string."""
    sep = "+" + "+".join("-" * w for w in _COL_WIDTHS) + "+"
    header_line = "|".join(_fmt(h, w) for h, w in zip(_HEADERS, _COL_WIDTHS))
    lines = [sep, f"|{header_line}|", sep]
    for row in rows:
        quota_str = f"{row.quota_used}/{row.quota_max}" if row.quota_max else "--"
        budget_str = f"{row.budget_used:.1f}s" if row.budget_max else "--"
        budget_max_str = f"{row.budget_max:.1f}s" if row.budget_max else "--"
        quota_max_str = str(row.quota_max) if row.quota_max else "--"
        cells = [
            row.job_name,
            str(row.quota_used) if row.quota_max else "--",
            quota_max_str,
            budget_str,
            budget_max_str,
        ]
        line = "|".join(_fmt(c, w) for c, w in zip(cells, _COL_WIDTHS))
        lines.append(f"|{line}|")
    lines.append(sep)
    return "\n".join(lines)
