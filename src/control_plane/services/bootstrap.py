from __future__ import annotations

import secrets
from datetime import timedelta

from common.errors import ValidationError
from common.timeutil import parse_iso_utc, utcnow
from control_plane.repo.sqlite import SQLiteRepo


class BootstrapService:
    def __init__(
        self, repo: SQLiteRepo, ttl_seconds: int = 3600, token_ttl_seconds: int = 86400
    ) -> None:
        self.repo = repo
        self.ttl_seconds = ttl_seconds
        self.token_ttl_seconds = token_ttl_seconds

    def issue_code(self) -> tuple[str, str]:
        code = secrets.token_urlsafe(12)
        expires_at = (utcnow() + timedelta(seconds=self.ttl_seconds)).isoformat()
        self.repo.insert_bootstrap_code(code, expires_at)
        return code, expires_at

    def consume_code(self, code: str, agent_name: str) -> tuple[str, str]:
        row = self.repo.get_bootstrap_code(code)
        if row is None:
            raise ValidationError(code="invalid_bootstrap_code", message="bootstrap_code not found")
        if row["consumed_at"] is not None:
            raise ValidationError(code="bootstrap_consumed", message="bootstrap_code already used")
        if parse_iso_utc(row["expires_at"]) < utcnow():
            raise ValidationError(code="bootstrap_expired", message="bootstrap_code expired")
        consumed = self.repo.consume_bootstrap_code(code, utcnow().isoformat(), agent_name)
        if not consumed:
            raise ValidationError(
                code="bootstrap_race", message="bootstrap_code consumed concurrently"
            )
        now = utcnow()
        token = secrets.token_urlsafe(24)
        expires_at = (now + timedelta(seconds=self.token_ttl_seconds)).isoformat()
        self.repo.insert_agent_token(token, agent_name, expires_at, now.isoformat())
        return token, expires_at
