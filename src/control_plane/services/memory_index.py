from __future__ import annotations

from common.errors import ValidationError
from common.models import MemoryRecord
from common.timeutil import parse_iso_utc, utcnow_iso
from control_plane.repo.sqlite import SQLiteRepo


class MemoryIndexService:
    def __init__(self, repo: SQLiteRepo) -> None:
        self.repo = repo

    def validate_reusable(self, record: MemoryRecord) -> None:
        if not record.oss_uri:
            raise ValidationError(code="missing_oss_uri", message="oss_uri is required")
        if not record.citations:
            raise ValidationError(
                code="missing_citation", message="at least one citation is required"
            )

    def save(self, record: MemoryRecord) -> None:
        self.validate_reusable(record)
        self.repo.insert_memory(record)

    def query_fresh(self) -> list[MemoryRecord]:
        now_iso = utcnow_iso()
        return self.repo.list_fresh_memory(now_iso)

    @staticmethod
    def infer_status(now_iso: str, fresh_until_iso: str, source_version_changed: bool) -> str:
        if source_version_changed:
            return "superseded"
        if parse_iso_utc(fresh_until_iso) <= parse_iso_utc(now_iso):
            return "stale"
        return "fresh"
