from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from common import settings as settings_module
from control_plane.app import create_app


class _Resp:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"ok": True}


def test_event_run_fanout_to_source_channel(tmp_path, monkeypatch) -> None:
    sent: list[tuple[str, dict]] = []

    def fake_post(url: str, json: dict | None = None, timeout: int = 10):
        _ = timeout
        sent.append((url, json or {}))
        return _Resp()

    monkeypatch.setattr(httpx, "post", fake_post)

    old_db = settings_module.settings.db_path
    old_oss = settings_module.settings.oss_root
    old_feishu = settings_module.settings.feishu_push_url
    old_imessage = settings_module.settings.imessage_push_url

    settings_module.settings.db_path = str(tmp_path / "cp.db")
    settings_module.settings.oss_root = str(tmp_path / "oss")
    settings_module.settings.feishu_push_url = "http://notify.local/feishu"
    settings_module.settings.imessage_push_url = "http://notify.local/imessage"

    try:
        app = create_app()
        with TestClient(app) as client:
            code = client.post("/api/bootstrap/new").json()["bootstrap_code"]
            reg = client.post(
                "/api/agents/register",
                json={"agent_name": "mbp-work", "agent_type": "mac_app", "bootstrap_code": code},
            )
            assert reg.status_code == 200

            ingest = client.post(
                "/api/tasks/ingest",
                json={
                    "task_id": "task-notify-1",
                    "source": "feishu",
                    "source_message_id": "msg-1",
                    "requester_id": "ou_123",
                    "target_agent": "mbp-work",
                    "project_alias": "backend",
                    "instruction": "fix",
                    "priority": 0,
                    "created_at": "2026-03-02T00:00:00+00:00",
                },
            )
            assert ingest.status_code == 200

            event = client.post(
                "/api/events/run",
                json={
                    "task_id": "task-notify-1",
                    "agent_name": "mbp-work",
                    "thread_id": "sess-1",
                    "event_type": "completed",
                    "summary": "all done",
                    "timestamp": "2026-03-02T00:01:00+00:00",
                },
            )
            assert event.status_code == 200
            assert event.json()["notify"]["status"] == "sent"
    finally:
        settings_module.settings.db_path = old_db
        settings_module.settings.oss_root = old_oss
        settings_module.settings.feishu_push_url = old_feishu
        settings_module.settings.imessage_push_url = old_imessage

    assert sent, "expected outbound notification"
    url, payload = sent[-1]
    assert url == "http://notify.local/feishu"
    assert payload["source"] == "feishu"
    assert payload["requester_id"] == "ou_123"
    assert "### Task Update" in payload["markdown"]
