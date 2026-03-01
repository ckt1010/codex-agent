from __future__ import annotations

from control_plane.repo.sqlite import SQLiteRepo


class DedupeService:
    def __init__(self, repo: SQLiteRepo) -> None:
        self.repo = repo

    def register(self, source: str, source_message_id: str, task_id: str, created_at: str) -> bool:
        return self.repo.add_task_dedup(source, source_message_id, task_id, created_at)
