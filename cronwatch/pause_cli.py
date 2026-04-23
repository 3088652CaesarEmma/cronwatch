"""CLI helpers for pause/resume commands.

Integrates with the main cronwatch CLI to expose:
  cronwatch pause <job>
  cronwatch resume <job>
  cronwatch paused
"""

from __future__ import annotations

import argparse
import sys

from cronwatch.pause import is_paused, list_paused, pause_job, resume_job


def add_pause_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register pause/resume/paused sub-commands on *subparsers*."""
    p_pause = subparsers.add_parser("pause", help="Pause a job so it is skipped during runs.")
    p_pause.add_argument("job", help="Name of the job to pause.")
    p_pause.set_defaults(func=cmd_pause)

    p_resume = subparsers.add_parser("resume", help="Resume a previously paused job.")
    p_resume.add_argument("job", help="Name of the job to resume.")
    p_resume.set_defaults(func=cmd_resume)

    p_paused = subparsers.add_parser("paused", help="List all currently paused jobs.")
    p_paused.set_defaults(func=cmd_list_paused)


def _get_log_dir(args: argparse.Namespace) -> str | None:
    """Extract the optional log_dir attribute from parsed arguments.

    Returns ``None`` if *args* does not carry a ``log_dir`` attribute, which
    causes the underlying pause helpers to fall back to their default
    directory.
    """
    return getattr(args, "log_dir", None)


def cmd_pause(args: argparse.Namespace) -> int:
    """Pause the specified job."""
    job_name: str = args.job
    log_dir = _get_log_dir(args)
    if is_paused(job_name, log_dir):
        print(f"Job '{job_name}' is already paused.", file=sys.stderr)
        return 1
    pause_job(job_name, log_dir)
    print(f"Job '{job_name}' paused.")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume the specified job."""
    job_name: str = args.job
    log_dir = _get_log_dir(args)
    if not is_paused(job_name, log_dir):
        print(f"Job '{job_name}' is not paused.", file=sys.stderr)
        return 1
    resume_job(job_name, log_dir)
    print(f"Job '{job_name}' resumed.")
    return 0


def cmd_list_paused(args: argparse.Namespace) -> int:
    """Print all currently paused jobs."""
    log_dir = _get_log_dir(args)
    paused = list_paused(log_dir)
    if not paused:
        print("No jobs are currently paused.")
    else:
        for name in paused:
            print(name)
    return 0
