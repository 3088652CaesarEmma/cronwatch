"""Cron job runner that executes commands and captures output/exit codes."""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class JobResult:
    """Result of a cron job execution."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    success: bool = field(init=False)

    def __post_init__(self):
        self.success = self.exit_code == 0

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILURE"
        return (
            f"[{status}] Command: {self.command!r} | "
            f"Exit code: {self.exit_code} | "
            f"Duration: {self.duration_seconds:.2f}s | "
            f"Started: {self.started_at.isoformat()}"
        )


def run_job(
    command: str,
    timeout: Optional[int] = None,
    shell: bool = True,
) -> JobResult:
    """Execute a shell command and return a JobResult.

    Args:
        command: The shell command to run.
        timeout: Optional timeout in seconds.
        shell: Whether to run via shell (default True).

    Returns:
        JobResult with execution details.

    Raises:
        subprocess.TimeoutExpired: If the command exceeds the timeout.
    """
    started_at = datetime.utcnow()
    start_time = time.monotonic()

    try:
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = -1
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = f"Command timed out after {timeout} seconds"

    finished_at = datetime.utcnow()
    duration_seconds = time.monotonic() - start_time

    return JobResult(
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
    )
