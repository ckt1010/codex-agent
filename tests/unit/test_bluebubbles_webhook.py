from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from connectors.bluebubbles_bridge import app, bridge


class _Resp:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_webhook_list_returns_markdown(monkeypatch) -> None:
    pushed: list[tuple[str, str]] = []

    def fake_get(url: str, timeout: int = 10):
        _ = (url, timeout)
        return _Resp({"markdown": "# Device Sessions\n"})

    def fake_push(recipient: str, markdown: str):
        pushed.append((recipient, markdown))
        return {"status": "sent"}

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(bridge.cmd, "push_markdown", fake_push)

    with TestClient(app) as client:
        res = client.post("/webhooks/bluebubbles", json={"text": "list", "sender": "+8613"})
    assert res.status_code == 200
    assert res.json()["status"] == "listed"
    assert "# Device Sessions" in res.json()["markdown"]
    assert any(item == ("+8613", "# Device Sessions\n") for item in pushed)


def test_webhook_task_accepted_pushes_markdown(monkeypatch) -> None:
    pushed: list[tuple[str, str]] = []

    def fake_ingest(sender: str, source_message_id: str, command):
        _ = source_message_id
        return {
            "task_id": "task-1",
            "control_plane": {"status": "accepted", "task_id": "task-1"},
            "session_id": command.session_id,
            "sender": sender,
        }

    def fake_push(recipient: str, markdown: str):
        pushed.append((recipient, markdown))
        return {"status": "sent"}

    monkeypatch.setattr(bridge.cmd, "ingest_to_control_plane", fake_ingest)
    monkeypatch.setattr(bridge.cmd, "push_markdown", fake_push)

    with TestClient(app) as client:
        res = client.post(
            "/webhooks/bluebubbles",
            json={"text": "@codex @agent:mbp-work @proj:backend fix bug", "sender": "+8613"},
        )
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"
    assert "### Task Accepted" in res.json()["markdown"]
    assert any(item[0] == "+8613" and "### Task Accepted" in item[1] for item in pushed)
