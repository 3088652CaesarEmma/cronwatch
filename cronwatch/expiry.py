"""Job expiry policy: skip jobs past a configured expiry date."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class JobExpiredError(Exception):
    def __init__(self, job_name: str, expiry: date):
        self.job_name = job_name
        self.expiry = expiry
        super().__init__(
            f"Job '{job_name}' expired on {expiry.isoformat()}"
        )


@dataclass
class ExpiryPolicy:
    expires_on: Optional[date] = None

    def __post_init__(self):
        if self.expires_on is not None and not isinstance(self.expires_on, date):
            raise TypeError("expires_on must be a date instance or None")

    @property
    def enabled(self) -> bool:
        return self.expires_on is not None

    def is_expired(self, today: Optional[date] = None) -> bool:
        if not self.enabled:
            return False
        today = today or datetime.utcnow().date()
        return today > self.expires_on

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "ExpiryPolicy":
        if not cfg:
            return cls()
        raw = cfg.get("expires_on")
        if raw is None:
            return cls()
        if isinstance(raw, date):
            return cls(expires_on=raw)
        return cls(expires_on=date.fromisoformat(str(raw)))
