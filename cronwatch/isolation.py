"""Job isolation policy: run jobs in a clean environment or temporary directory."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IsolationPolicy:
    """Controls whether a job runs in an isolated working directory."""

    use_tmpdir: bool = False
    clean_env: bool = False
    allowed_vars: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.use_tmpdir, bool):
            raise TypeError("use_tmpdir must be a bool")
        if not isinstance(self.clean_env, bool):
            raise TypeError("clean_env must be a bool")
        if not isinstance(self.allowed_vars, list):
            raise TypeError("allowed_vars must be a list")
        for v in self.allowed_vars:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("Each allowed_vars entry must be a non-empty string")
        self.allowed_vars = [v.strip() for v in self.allowed_vars]

    @property
    def enabled(self) -> bool:
        return self.use_tmpdir or self.clean_env

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "IsolationPolicy":
        if not cfg:
            return cls()
        return cls(
            use_tmpdir=bool(cfg.get("use_tmpdir", False)),
            clean_env=bool(cfg.get("clean_env", False)),
            allowed_vars=list(cfg.get("allowed_vars") or []),
        )

    def build_env(self) -> Optional[dict]:
        """Return the environment mapping for the job, or None to inherit."""
        if not self.clean_env:
            return None
        base = {k: v for k, v in os.environ.items() if k in self.allowed_vars}
        return base

    def make_workdir(self) -> Optional[str]:
        """Create and return a temporary working directory, or None."""
        if not self.use_tmpdir:
            return None
        return tempfile.mkdtemp(prefix="cronwatch_")
