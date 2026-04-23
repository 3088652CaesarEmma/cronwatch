"""CLI subcommands for inspecting and clearing job watermarks."""
from __future__ import annotations

import argparse
import os

from cronwatch.watermark import get_watermark_path, load_watermarks, save_watermarks
from cronwatch.log import get_log_dir


def add_watermark_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    show_p = subparsers.add_parser("watermark-show", help="Show high-watermark stats for a job")
    show_p.add_argument("job", help="Job name")
    show_p.set_defaults(func=cmd_watermark_show)

    clear_p = subparsers.add_parser("watermark-clear", help="Clear high-watermark stats for a job")
    clear_p.add_argument("job", help="Job name")
    clear_p.set_defaults(func=cmd_watermark_clear)


def _get_log_dir(args: argparse.Namespace) -> str:
    return getattr(args, "log_dir", None) or get_log_dir()


def cmd_watermark_show(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir(args)
    marks = load_watermarks(args.job, log_dir)
    if not marks:
        print(f"No watermark data for job '{args.job}'.")
        return
    print(f"Watermarks for '{args.job}':")
    for key, value in sorted(marks.items()):
        print(f"  {key}: {value}")


def cmd_watermark_clear(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir(args)
    path = get_watermark_path(args.job, log_dir)
    if os.path.exists(path):
        os.remove(path)
        print(f"Watermarks cleared for job '{args.job}'.")
    else:
        print(f"No watermark data found for job '{args.job}'.")
