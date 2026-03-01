from __future__ import annotations

import pytest

from common.errors import ValidationError
from common.models import Citation, MemoryRecord
from control_plane.repo.sqlite import SQLiteRepo
from control_plane.services.memory_index import MemoryIndexService


def _record(**kwargs) -> MemoryRecord:
    base = {
        "memory_id": "mem-1",
        "source_type": "pdf",
        "source_doc_id": "doc-1",
        "source_version": "v1",
        "oss_uri": "oss://bucket/doc-1",
        "visibility": "system",
        "owner": "codex-bot",
        "summary": "summary",
        "conclusions": "conclusion",
        "key_pages": [3],
        "evidence_snippets": ["snippet"],
        "citations": [
            Citation(
                source_doc_id="doc-1",
                page=3,
                snippet_hash="abc",
                snippet_text="snippet",
                locator="pdf://doc-1#page=3",
            )
        ],
        "extracted_at": "2026-03-01T00:00:00+00:00",
        "extracted_by_agent": "mbp-work",
        "ttl_seconds": 3600,
        "fresh_until": "2099-01-01T00:00:00+00:00",
        "status": "fresh",
    }
    base.update(kwargs)
    return MemoryRecord(**base)


def test_ttl_expired_marks_stale() -> None:
    status = MemoryIndexService.infer_status(
        now_iso="2026-03-02T00:00:00+00:00",
        fresh_until_iso="2026-03-01T00:00:00+00:00",
        source_version_changed=False,
    )
    assert status == "stale"


def test_source_version_change_marks_superseded() -> None:
    status = MemoryIndexService.infer_status(
        now_iso="2026-03-01T00:00:00+00:00",
        fresh_until_iso="2099-01-01T00:00:00+00:00",
        source_version_changed=True,
    )
    assert status == "superseded"


def test_missing_oss_uri_returns_explicit_error(tmp_path) -> None:
    repo = SQLiteRepo(str(tmp_path / "db.sqlite"))
    svc = MemoryIndexService(repo)

    with pytest.raises(ValidationError, match="oss_uri is required"):
        svc.save(_record(oss_uri=""))


def test_missing_citation_not_reusable(tmp_path) -> None:
    repo = SQLiteRepo(str(tmp_path / "db.sqlite"))
    svc = MemoryIndexService(repo)

    with pytest.raises(ValidationError, match="at least one citation is required"):
        svc.save(_record(citations=[]))
