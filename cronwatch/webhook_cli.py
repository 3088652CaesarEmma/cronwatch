"""CLI helpers for webhook subcommands (test-webhook)."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.runner import JobResult
from cronwatch.webhook import WebhookPolicy, send_webhook


def add_webhook_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'test-webhook' subcommand."""
    p = subparsers.add_parser(
        "test-webhook",
        help="Send a test webhook payload to the configured endpoint",
    )
    p.add_argument(
        "--url",
        default=None,
        help="Override the webhook URL from config",
    )
    p.add_argument(
        "--config",
        default=None,
        metavar="FILE",
        help="Path to cronwatch config file",
    )
    p.set_defaults(func=cmd_test_webhook)


def cmd_test_webhook(args: argparse.Namespace) -> int:
    """Send a synthetic webhook payload and report the outcome."""
    cfg = load_config(args.config if hasattr(args, "config") else None)
    webhook_cfg = getattr(cfg, "webhook", None)
    policy = WebhookPolicy.from_config(webhook_cfg) if isinstance(webhook_cfg, dict) else WebhookPolicy()

    if args.url:
        policy = WebhookPolicy(
            url=args.url,
            method=policy.method,
            headers=policy.headers,
            timeout=policy.timeout,
            on_failure=True,
            on_success=True,
        )

    if not policy.enabled:
        print("No webhook URL configured. Use --url or set webhook.url in config.", file=sys.stderr)
        return 1

    dummy = JobResult(
        command="cronwatch/test-webhook",
        exit_code=0,
        stdout="This is a test payload from cronwatch.",
        stderr="",
        duration=0.0,
    )
    # Force delivery regardless of on_success setting
    policy = WebhookPolicy(
        url=policy.url,
        method=policy.method,
        headers=policy.headers,
        timeout=policy.timeout,
        on_failure=True,
        on_success=True,
    )
    ok = send_webhook(dummy, policy)
    if ok:
        print(f"Webhook delivered successfully to {policy.url}")
        return 0
    else:
        print(f"Webhook delivery failed to {policy.url}", file=sys.stderr)
        return 2
