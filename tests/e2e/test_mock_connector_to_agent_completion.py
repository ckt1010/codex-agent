from __future__ import annotations

from urllib.parse import urlparse

import httpx

from agent_ubuntu.runner import UbuntuAgentRunner
from connectors.mock_feishu import MockFeishuConnector


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self) -> dict:
        return self._payload


def test_feishu_ingest_to_agent_completed_event(client, monkeypatch) -> None:
    def fake_post(url: str, json: dict | None = None, timeout: int = 10):
        _ = timeout
        parsed = urlparse(url)
        path = parsed.path
        response = client.post(path, json=json)
        return _Resp(response.status_code, response.json())

    monkeypatch.setattr(httpx, "post", fake_post)

    code = client.post("/api/bootstrap/new").json()["bootstrap_code"]
    register = client.post(
        "/api/agents/register",
        json={"agent_name": "ubuntu-dev-1", "agent_type": "ubuntu_cli", "bootstrap_code": code},
    )
    assert register.status_code == 200

    connector = MockFeishuConnector("http://local")
    ingest = connector.ingest(
        {
            "task_id": "task-e2e-1",
            "source": "feishu",
            "source_message_id": "feishu-msg-1",
            "requester_id": "user-1",
            "target_agent": "ubuntu-dev-1",
            "project_alias": "backend",
            "instruction": "run e2e",
            "priority": 1,
            "created_at": "2026-03-01T00:00:00+00:00",
        }
    )
    assert ingest["status"] == "accepted"

    runner = UbuntuAgentRunner("http://local", "ubuntu-dev-1")
    runner.heartbeat()
    done = runner.pull_once()
    assert done["status"] == "completed"

    pull_after = client.post("/api/agents/pull-task", json={"agent_name": "ubuntu-dev-1"}).json()
    assert pull_after["task"] is None


def test_system_visibility_isolation_assertion(client) -> None:
    create = client.post(
        "/api/memory/index",
        json={
            "memory_id": "sys-1",
            "source_type": "pdf",
            "source_doc_id": "doc-sys",
            "source_version": "v1",
            "oss_uri": "oss://demo/sys.txt",
            "visibility": "system",
            "owner": "codex-bot",
            "summary": "s",
            "conclusions": "c",
            "key_pages": [1],
            "evidence_snippets": ["x"],
            "citations": [
                {
                    "source_doc_id": "doc-sys",
                    "page": 1,
                    "snippet_hash": "h",
                    "snippet_text": "x",
                    "locator": "pdf://doc-sys#page=1",
                }
            ],
            "extracted_at": "2026-03-01T00:00:00+00:00",
            "extracted_by_agent": "ubuntu-dev-1",
            "ttl_seconds": 3600,
            "fresh_until": "2099-01-01T00:00:00+00:00",
            "status": "fresh",
        },
    )
    assert create.status_code == 200

    index = client.get("/api/memory/index").json()["records"]
    assert any(r["memory_id"] == "sys-1" and r["visibility"] == "system" for r in index)
