from __future__ import annotations

from control_plane.repo.sqlite import SQLiteRepo
from control_plane.services.dedupe import DedupeService


def test_dedupe_register_only_once(tmp_path) -> None:
    repo = SQLiteRepo(str(tmp_path / "db.sqlite"))
    dedupe = DedupeService(repo)

    first = dedupe.register("feishu", "msg-1", "task-1", "2026-03-01T00:00:00+00:00")
    second = dedupe.register("feishu", "msg-1", "task-2", "2026-03-01T00:00:01+00:00")

    assert first is True
    assert second is False
