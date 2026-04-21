"""Context manager that fires a webhook after a job completes."""
from __future__ import annotations

from cronwatch.runner import JobResult
from cronwatch.webhook import WebhookPolicy, send_webhook


class WebhookGuard:
    """Fires a webhook notification when the guarded block exits.

    Usage::

        with WebhookGuard(policy) as guard:
            result = run_job(command)
            guard.result = result
    """

    def __init__(self, policy: WebhookPolicy) -> None:
        self.policy = policy
        self.result: JobResult | None = None

    def __enter__(self) -> "WebhookGuard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.result is not None and self.policy.enabled:
            send_webhook(self.result, self.policy)
        return False
