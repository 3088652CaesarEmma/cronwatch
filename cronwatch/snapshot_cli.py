"""CLI sub-commands for managing job output snapshots."""
from __future__ import annotations

import argparse

from cronwatch.snapshots import get_snapshot_path, load_snapshot, save_snapshot


def add_snapshot_subcommands(subparsers: argparse._SubParsersAction) -> None:
    show_p = subparsers.add_parser("snapshot-show", help="Show stored snapshot for a job")
    show_p.add_argument("job", help="Job name")
    show_p.set_defaults(func=cmd_snapshot_show)

    clear_p = subparsers.add_parser("snapshot-clear", help="Delete stored snapshot for a job")
    clear_p.add_argument("job", help="Job name")
    clear_p.set_defaults(func=cmd_snapshot_clear)


def cmd_snapshot_show(args: argparse.Namespace) -> None:
    snapshot = load_snapshot(args.job)
    if snapshot is None:
        print(f"No snapshot stored for job '{args.job}'.")
        return
    print(f"Job:  {args.job}")
    print(f"Hash: {snapshot['hash']}")
    if "output" in snapshot:
        print("Output:")
        print(snapshot["output"])


def cmd_snapshot_clear(args: argparse.Namespace) -> None:
    path = get_snapshot_path(args.job)
    if path.exists():
        path.unlink()
        print(f"Snapshot for '{args.job}' cleared.")
    else:
        print(f"No snapshot found for '{args.job}'.")
