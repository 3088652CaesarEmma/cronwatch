"""Pre/post execution hooks for cronwatch jobs."""

import subprocess
import logging
from dataclasses import dataclass, field
from typing import Callable

from cronwatch.runner import JobResult

logger = logging.getLogger("cronwatch.hooks")

HookFn = Callable[[JobResult], None]


@dataclass
class HookRegistry:
    """Registry of callables to run before or after a job."""

    pre_hooks: list[HookFn] = field(default_factory=list)
    post_hooks: list[HookFn] = field(default_factory=list)

    def register_pre(self, fn: HookFn) -> None:
        self.pre_hooks.append(fn)

    def register_post(self, fn: HookFn) -> None:
        self.post_hooks.append(fn)

    def run_pre(self, result: JobResult) -> None:
        for hook in self.pre_hooks:
            try:
                hook(result)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Pre-hook %s raised: %s", hook, exc)

    def run_post(self, result: JobResult) -> None:
        for hook in self.post_hooks:
            try:
                hook(result)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Post-hook %s raised: %s", hook, exc)


def shell_hook(command: str) -> HookFn:
    """Return a hook that runs *command* in a shell, passing job metadata via env."""

    def _hook(result: JobResult) -> None:
        env_extra = {
            "CRONWATCH_JOB": result.job_name,
            "CRONWATCH_EXIT_CODE": str(result.exit_code),
            "CRONWATCH_DURATION": str(round(result.duration, 3)),
        }
        import os
        env = {**os.environ, **env_extra}
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != 0:
            logger.warning(
                "Shell hook '%s' exited %d: %s",
                command,
                proc.returncode,
                proc.stderr.strip(),
            )

    return _hook


def on_failure_hook(fn: HookFn) -> HookFn:
    """Wrap *fn* so it only fires when the job has a non-zero exit code."""

    def _hook(result: JobResult) -> None:
        if result.exit_code != 0:
            fn(result)

    return _hook


def on_success_hook(fn: HookFn) -> HookFn:
    """Wrap *fn* so it only fires when the job exits with code 0."""

    def _hook(result: JobResult) -> None:
        if result.exit_code == 0:
            fn(result)

    return _hook


# Module-level default registry used by the CLI pipeline.
default_registry = HookRegistry()
