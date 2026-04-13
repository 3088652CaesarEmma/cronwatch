"""Environment variable injection for cron job execution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvironPolicy:
    """Policy for injecting and managing environment variables for a job."""

    vars: Dict[str, str] = field(default_factory=dict)
    inherit: bool = True
    clear_keys: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.vars, dict):
            raise TypeError("vars must be a dict")
        if not isinstance(self.clear_keys, list):
            raise TypeError("clear_keys must be a list")

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "EnvironPolicy":
        """Build an EnvironPolicy from a config dict (or None for defaults)."""
        if not cfg:
            return cls()
        return cls(
            vars=cfg.get("vars", {}),
            inherit=cfg.get("inherit", True),
            clear_keys=cfg.get("clear_keys", []),
        )

    def build_env(self) -> Dict[str, str]:
        """Return the environment dict to pass to subprocess.

        If *inherit* is True the current process environment is used as a
        base; otherwise an empty environment is started from scratch.  The
        *vars* mapping is then merged in and any keys listed in *clear_keys*
        are removed.
        """
        env: Dict[str, str] = dict(os.environ) if self.inherit else {}
        env.update(self.vars)
        for key in self.clear_keys:
            env.pop(key, None)
        return env

    @property
    def enabled(self) -> bool:
        """Return True when this policy actually modifies the environment."""
        return bool(self.vars or self.clear_keys or not self.inherit)
