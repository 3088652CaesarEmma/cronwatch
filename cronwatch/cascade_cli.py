"""CLI subcommands for inspecting and managing cascade job chains."""

from __future__ import annotations

import argparse
from typing import List

from cronwatch.cascade import CascadePolicy
from cronwatch.jobs import load_jobs_from_config
from cronwatch.config import load_config


def add_cascade_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Register cascade-related subcommands onto the given subparser group."""
    cascade_parser = subparsers.add_parser(
        "cascade",
        help="Inspect cascade (job chain) configuration",
    )
    cascade_sub = cascade_parser.add_subparsers(
        dest="cascade_cmd", metavar="CASCADE_CMD"
    )

    # cascade show <job>
    show_parser = cascade_sub.add_parser(
        "show",
        help="Show the cascade chain for a named job",
    )
    show_parser.add_argument("job", help="Job name to inspect")
    show_parser.set_defaults(func=cmd_cascade_show)

    # cascade list
    list_parser = cascade_sub.add_parser(
        "list",
        help="List all jobs that have cascade rules configured",
    )
    list_parser.set_defaults(func=cmd_cascade_list)


def _load_all_jobs(args: argparse.Namespace):
    """Load jobs from the config file referenced in args (or default)."""
    config_path = getattr(args, "config", None)
    cfg = load_config(config_path)
    return load_jobs_from_config(cfg)


def cmd_cascade_show(args: argparse.Namespace) -> int:
    """Print the on_success / on_failure cascade chains for a single job.

    Returns 0 on success, 1 if the job is not found.
    """
    jobs = _load_all_jobs(args)
    target = next((j for j in jobs if j.name == args.job), None)
    if target is None:
        print(f"[cascade] Job '{args.job}' not found.")
        return 1

    policy_cfg = getattr(target, "cascade", None)
    policy = CascadePolicy.from_config(policy_cfg) if isinstance(policy_cfg, dict) else CascadePolicy()

    if not policy.enabled:
        print(f"[cascade] Job '{args.job}' has no cascade rules configured.")
        return 0

    on_success = policy.jobs_for(success=True)
    on_failure = policy.jobs_for(success=False)

    print(f"Cascade chains for job: {args.job}")
    print()
    if on_success:
        print("  on_success:")
        for name in on_success:
            print(f"    - {name}")
    else:
        print("  on_success: (none)")

    if on_failure:
        print("  on_failure:")
        for name in on_failure:
            print(f"    - {name}")
    else:
        print("  on_failure: (none)")

    return 0


def cmd_cascade_list(args: argparse.Namespace) -> int:
    """List every job that has at least one cascade rule.

    Returns 0 always.
    """
    jobs = _load_all_jobs(args)
    found: List[str] = []

    for job in jobs:
        policy_cfg = getattr(job, "cascade", None)
        policy = (
            CascadePolicy.from_config(policy_cfg)
            if isinstance(policy_cfg, dict)
            else CascadePolicy()
        )
        if policy.enabled:
            found.append(job.name)

    if not found:
        print("No jobs have cascade rules configured.")
        return 0

    print(f"Jobs with cascade rules ({len(found)}):")
    for name in sorted(found):
        print(f"  {name}")

    return 0
