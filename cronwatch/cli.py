"""CLI entry point for cronwatch."""

import argparse
import sys
from datetime import datetime

from cronwatch.config import load_config
from cronwatch.jobs import load_jobs_from_config, find_job_by_name, filter_jobs_by_tag
from cronwatch.runner import run_job
from cronwatch.notifier import notify
from cronwatch.scheduler import get_due_jobs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor, log, and alert on cron job failures.",
    )
    parser.add_argument(
        "--config", "-c",
        default="cronwatch.yml",
        help="Path to cronwatch config file (default: cronwatch.yml)",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a specific job by name")
    run_parser.add_argument("job_name", help="Name of the job to run")

    subparsers.add_parser("run-due", help="Run all jobs that are currently due")

    list_parser = subparsers.add_parser("list", help="List configured jobs")
    list_parser.add_argument(
        "--tag", "-t", default=None, help="Filter jobs by tag"
    )

    return parser


def cmd_run(job_name: str, config_path: str) -> int:
    config = load_config(config_path)
    jobs = load_jobs_from_config(config)
    job = find_job_by_name(jobs, job_name)
    if job is None:
        print(f"Error: job '{job_name}' not found.", file=sys.stderr)
        return 2
    result = run_job(job.command, job.name)
    notify(result, config)
    print(result.summary())
    return 0 if result.exit_code == 0 else 1


def cmd_run_due(config_path: str) -> int:
    config = load_config(config_path)
    jobs = load_jobs_from_config(config)
    now = datetime.now()
    due = get_due_jobs(jobs, now)
    if not due:
        print("No jobs are due at this time.")
        return 0
    exit_codes = []
    for job in due:
        result = run_job(job.command, job.name)
        notify(result, config)
        print(result.summary())
        exit_codes.append(result.exit_code)
    return 0 if all(c == 0 for c in exit_codes) else 1


def cmd_list(config_path: str, tag: str | None) -> int:
    config = load_config(config_path)
    jobs = load_jobs_from_config(config)
    if tag:
        jobs = filter_jobs_by_tag(jobs, tag)
    if not jobs:
        print("No jobs found.")
        return 0
    for job in jobs:
        tags_str = ", ".join(job.tags) if job.tags else "-"
        status = "enabled" if job.enabled else "disabled"
        print(f"  {job.name:<30} [{status}]  tags: {tags_str}  schedule: {job.schedule}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args.job_name, args.config)
    elif args.command == "run-due":
        return cmd_run_due(args.config)
    elif args.command == "list":
        return cmd_list(args.config, getattr(args, "tag", None))
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
