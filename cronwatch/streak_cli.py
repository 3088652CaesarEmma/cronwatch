"""CLI sub-commands for inspecting job streaks."""
from __future__ import annotations

import argparse
import os

from cronwatch.log import get_log_dir
from cronwatch.streak import get_streak, load_streaks


def add_streak_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    show_p = subparsers.add_parser("streak-show", help="Show streak for a specific job")
    show_p.add_argument("job_name", help="Name / command of the job")
    show_p.set_defaults(func=cmd_streak_show)

    list_p = subparsers.add_parser("streak-list", help="List streaks for all jobs")
    list_p.set_defaults(func=cmd_streak_list)


def _get_log_dir(args: argparse.Namespace) -> str:
    return getattr(args, "log_dir", None) or get_log_dir()


def cmd_streak_show(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir(args)
    state = get_streak(args.job_name, log_dir=log_dir)
    if state is None:
        print(f"No streak data found for job: {args.job_name}")
        return
    _print_state(state)


def cmd_streak_list(args: argparse.Namespace) -> None:
    log_dir = _get_log_dir(args)
    states = load_streaks(log_dir)
    if not states:
        print("No streak data recorded yet.")
        return
    for state in sorted(states.values(), key=lambda s: s.job_name):
        _print_state(state)
        print()


def _print_state(state) -> None:
    direction = "success" if state.current >= 0 else "failure"
    count = abs(state.current)
    print(f"Job         : {state.job_name}")
    print(f"Current     : {count} consecutive {direction}(s)")
    print(f"Best run    : {state.best_success} consecutive successes")
    print(f"Worst run   : {state.worst_failure} consecutive failures")
