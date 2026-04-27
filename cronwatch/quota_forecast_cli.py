"""CLI subcommands for quota forecasting."""
from __future__ import annotations

import argparse
import sys

from cronwatch.jobs import load_jobs_from_config
from cronwatch.log import get_log_dir
from cronwatch.quota import QuotaPolicy
from cronwatch.quota_forecast import forecast_quota


def add_quota_forecast_subcommands(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "quota-forecast",
        help="Show projected quota exhaustion for one or all jobs",
    )
    p.add_argument(
        "--job",
        metavar="NAME",
        default=None,
        help="Forecast for a specific job (default: all jobs)",
    )
    p.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to cronwatch config file",
    )
    p.set_defaults(func=cmd_quota_forecast)


def cmd_quota_forecast(args: argparse.Namespace) -> None:
    from cronwatch.config import load_config

    cfg = load_config(args.config if hasattr(args, "config") else None)
    log_dir = get_log_dir(cfg)

    try:
        jobs = load_jobs_from_config(cfg)
    except Exception as exc:  # pragma: no cover
        print(f"Error loading jobs: {exc}", file=sys.stderr)
        sys.exit(1)

    target_name: str | None = getattr(args, "job", None)
    found_any = False

    for job in jobs:
        if target_name and job.name != target_name:
            continue
        found_any = True
        quota_cfg = getattr(job, "quota", None)
        policy = QuotaPolicy.from_config(quota_cfg)
        if not policy.enabled:
            print(f"{job.name}: quota not enabled")
            continue
        result = forecast_quota(job.name, policy, log_dir)
        if result is None:
            print(f"{job.name}: quota not enabled")
        else:
            print(result.summary)

    if target_name and not found_any:
        print(f"No job named '{target_name}' found.", file=sys.stderr)
        sys.exit(1)
