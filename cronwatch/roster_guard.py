"""Guard that prevents running jobs not present in the roster."""
from __future__ import annotations

from typing import Optional

from cronwatch.roster import load_roster, register_job


class JobNotRegisteredError(Exception):
    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        super().__init__(f"Job '{job_name}' is not registered in the roster")


class RosterGuard:
    """Context manager that checks job roster membership before allowing execution.

    If ``auto_register`` is True the job is silently added to the roster on
    first encounter instead of raising an error.
    """

    def __init__(
        self,
        job_name: str,
        command: str,
        *,
        auto_register: bool = False,
        log_dir: Optional[str] = None,
    ) -> None:
        self.job_name = job_name
        self.command = command
        self.auto_register = auto_register
        self.log_dir = log_dir

    def __enter__(self) -> "RosterGuard":
        roster = load_roster(self.log_dir)
        if self.job_name not in roster:
            if self.auto_register:
                register_job(self.job_name, self.command, log_dir=self.log_dir)
            else:
                raise JobNotRegisteredError(self.job_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
