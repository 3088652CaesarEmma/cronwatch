"""Context manager guard that enforces the circuit breaker policy."""

from __future__ import annotations

from cronwatch.circuit_breaker import CircuitBreakerPolicy, is_open


class CircuitOpenError(Exception):
    """Raised when a job is skipped because its circuit breaker is open."""

    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        super().__init__(
            f"Circuit breaker is open for job '{job_name}'; skipping execution."
        )


class CircuitBreakerGuard:
    """Skips job execution when the circuit breaker is open.

    Usage::

        with CircuitBreakerGuard(policy, log_dir, job_name):
            result = run_job(job)
    """

    def __init__(
        self,
        policy: CircuitBreakerPolicy,
        log_dir: str,
        job_name: str,
    ) -> None:
        self._policy = policy
        self._log_dir = log_dir
        self._job_name = job_name

    def __enter__(self) -> "CircuitBreakerGuard":
        if is_open(self._log_dir, self._job_name, self._policy):
            raise CircuitOpenError(self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
