"""CLI subcommands for quota rollover management."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.log import get_log_dir
from cronwatch.quota import load_quota_state, save_quota_state
from cronwatch.quota_rollover import (
    QuotaRolloverPolicy,
    get_rollover_state_path,
    load_rollover_state,
    save_rollover_state,
)


def add_quota_rollover_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    status_p = subparsers.add_parser("rollover-status", help="Show quota rollover state for a job")
    status_p.add_argument("job", help="Job name")
    status_p.set_defaults(func=cmd_rollover_status)

    reset_p = subparsers.add_parser("rollover-reset", help="Manually reset quota rollover state for a job")
    reset_p.add_argument("job", help="Job name")
    reset_p.set_defaults(func=cmd_rollover_reset)


def _get_log_dir() -> Path:
    return get_log_dir()


def cmd_rollover_status(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir()
    state = load_rollover_state(args.job, log_dir)
    if not state:
        print(f"No rollover state recorded for job '{args.job}'.")
        return
    bucket = state.get("bucket", "unknown")
    runs = load_quota_state(args.job, log_dir)
    print(f"Job:     {args.job}")
    print(f"Bucket:  {bucket}")
    print(f"Runs in current period: {len(runs)}")


def cmd_rollover_reset(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir()
    save_rollover_state(args.job, {}, log_dir)
    save_quota_state(args.job, [], log_dir)
    print(f"Rollover state and quota counts reset for job '{args.job}'.")
