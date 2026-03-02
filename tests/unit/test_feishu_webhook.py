from __future__ import annotations

from fastapi.testclient import TestClient

from connectors.feishu_bridge import app, bridge


def test_feishu_list_pushes_markdown(monkeypatch) -> None:
    pushed: list[tuple[str, str]] = []

    def fake_markdown() -> str:
        return "# Device Sessions\n"

    def fake_push(recipient: str, markdown: str):
        pushed.append((recipient, markdown))
        return {"status": "sent"}

    monkeypatch.setattr(bridge.cmd, "get_sessions_markdown", fake_markdown)
    monkeypatch.setattr(bridge.cmd, "push_markdown", fake_push)

    payload = {
        "event": {
            "sender": {"sender_id": {"open_id": "ou_123"}},
            "message": {"content": '{"text":"list"}', "message_id": "m1"},
        }
    }
    with TestClient(app) as client:
        res = client.post("/webhooks/feishu", json=payload)

    assert res.status_code == 200
    assert res.json()["status"] == "listed"
    assert any(item == ("ou_123", "# Device Sessions\n") for item in pushed)
