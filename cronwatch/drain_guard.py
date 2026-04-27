"""Context manager that registers / deregisters a job with DrainCoordinator."""
from __future__ import annotations

from cronwatch.drain import DrainCoordinator


class DrainGuard:
    """Registers a job as active on enter and releases it on exit.

    Usage::

        with DrainGuard(coordinator, "backup"):
            run_job(...)
    """

    def __init__(self, coordinator: DrainCoordinator, job_name: str) -> None:
        self._coordinator = coordinator
        self._job_name = job_name

    def __enter__(self) -> "DrainGuard":
        self._coordinator.acquire(self._job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._coordinator.release(self._job_name)
        return False  # never suppress exceptions
