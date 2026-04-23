"""quota_budget_cli.py — CLI subcommands for quota+budget status reporting."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwatch.config import load_config
from cronwatch.quota import QuotaPolicy
from cronwatch.budget import BudgetPolicy
from cronwatch.log import get_log_dir


def add_quota_budget_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register ``quota-status`` and ``budget-status`` sub-commands."""
    p_quota = subparsers.add_parser(
        "quota-status",
        help="Show run-count quota usage for a job.",
    )
    p_quota.add_argument("job", help="Job name to inspect.")
    p_quota.add_argument("--config", default=None, help="Path to config file.")
    p_quota.set_defaults(func=cmd_quota_status)

    p_budget = subparsers.add_parser(
        "budget-status",
        help="Show runtime budget usage for a job.",
    )
    p_budget.add_argument("job", help="Job name to inspect.")
    p_budget.add_argument("--config", default=None, help="Path to config file.")
    p_budget.set_defaults(func=cmd_budget_status)


def cmd_quota_status(args: argparse.Namespace) -> None:
    """Print quota usage for *args.job*."""
    cfg = load_config(args.config)
    log_dir = get_log_dir(cfg)
    job_cfg = (cfg.jobs or {}).get(args.job, {})
    policy = QuotaPolicy.from_config(job_cfg.get("quota"))

    if not policy.enabled:
        print(f"Quota not enabled for '{args.job}'.")
        return

    used = policy.get_run_count(args.job, log_dir)
    print(
        f"Job '{args.job}': {used} / {policy.max_runs} runs used "
        f"in the last {policy.window_seconds}s window."
    )


def cmd_budget_status(args: argparse.Namespace) -> None:
    """Print budget usage for *args.job*."""
    cfg = load_config(args.config)
    log_dir = get_log_dir(cfg)
    job_cfg = (cfg.jobs or {}).get(args.job, {})
    policy = BudgetPolicy.from_config(job_cfg.get("budget"))

    if not policy.enabled:
        print(f"Budget not enabled for '{args.job}'.")
        return

    used = policy.get_used_seconds(args.job, log_dir)
    remaining = max(0.0, policy.max_seconds - used)
    print(
        f"Job '{args.job}': {used:.1f}s used of {policy.max_seconds:.1f}s budget "
        f"({remaining:.1f}s remaining)."
    )
