from __future__ import annotations


def test_memory_query_flow_index_then_oss(client) -> None:
    app = client.app
    app.state.oss.put_text("oss://demo/doc1.txt", "evidence content")

    create = client.post(
        "/api/memory/index",
        json={
            "memory_id": "mem-1",
            "source_type": "pdf",
            "source_doc_id": "doc-1",
            "source_version": "v1",
            "oss_uri": "oss://demo/doc1.txt",
            "visibility": "system",
            "owner": "codex-bot",
            "summary": "summary",
            "conclusions": "conclusion",
            "key_pages": [2],
            "evidence_snippets": ["snippet"],
            "citations": [
                {
                    "source_doc_id": "doc-1",
                    "page": 2,
                    "snippet_hash": "h1",
                    "snippet_text": "snippet",
                    "locator": "pdf://doc-1#page=2",
                }
            ],
            "extracted_at": "2026-03-01T00:00:00+00:00",
            "extracted_by_agent": "mbp-work",
            "ttl_seconds": 3600,
            "fresh_until": "2099-01-01T00:00:00+00:00",
            "status": "fresh",
        },
    )
    assert create.status_code == 200

    index = client.get("/api/memory/index")
    assert index.status_code == 200
    records = index.json()["records"]
    assert len(records) == 1
    assert records[0]["memory_id"] == "mem-1"

    content = client.get("/api/memory/content", params={"oss_uri": records[0]["oss_uri"]})
    assert content.status_code == 200
    assert content.json()["content"] == "evidence content"


def test_memory_missing_oss_uri_returns_error(client) -> None:
    create = client.post(
        "/api/memory/index",
        json={
            "memory_id": "mem-2",
            "source_type": "pdf",
            "source_doc_id": "doc-2",
            "source_version": "v1",
            "oss_uri": "",
            "visibility": "system",
            "owner": "codex-bot",
            "summary": "summary",
            "conclusions": "conclusion",
            "key_pages": [1],
            "evidence_snippets": ["s"],
            "citations": [
                {
                    "source_doc_id": "doc-2",
                    "page": 1,
                    "snippet_hash": "h2",
                    "snippet_text": "s",
                    "locator": "pdf://doc-2#page=1",
                }
            ],
            "extracted_at": "2026-03-01T00:00:00+00:00",
            "extracted_by_agent": "mbp-home",
            "ttl_seconds": 3600,
            "fresh_until": "2099-01-01T00:00:00+00:00",
            "status": "fresh",
        },
    )

    assert create.status_code == 400
    assert "oss_uri" in create.json()["detail"]
