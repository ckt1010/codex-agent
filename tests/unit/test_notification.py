from __future__ import annotations

import httpx

from control_plane.services.notification import NotificationFanout


class _Resp:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"ok": True}


def test_notify_system_status_to_both_channels(monkeypatch) -> None:
    sent: list[tuple[str, dict]] = []

    def fake_post(url: str, json: dict | None = None, timeout: int = 10):
        _ = timeout
        sent.append((url, json or {}))
        return _Resp()

    monkeypatch.setattr(httpx, "post", fake_post)

    fanout = NotificationFanout(
        feishu_push_url="http://push.local/feishu",
        imessage_push_url="http://push.local/imessage",
        timeout_seconds=5,
    )
    result = fanout.notify_system_status("control-plane", "started", "ok")

    assert result["feishu"]["status"] == "sent"
    assert result["imessage"]["status"] == "sent"
    assert len(sent) == 2


def test_notify_task_event_failure_does_not_raise(monkeypatch) -> None:
    def fake_post(url: str, json: dict | None = None, timeout: int = 10):
        _ = (url, json, timeout)
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", fake_post)

    fanout = NotificationFanout(feishu_push_url="http://push.local/feishu")
    result = fanout.notify_task_event(
        task={
            "source": "feishu",
            "task_id": "t1",
            "requester_id": "u1",
            "project_alias": "p",
            "session_id": "s1",
        },
        event={
            "agent_name": "mbp",
            "event_type": "completed",
            "timestamp": "2026-03-02T00:00:00+00:00",
            "summary": "done",
            "thread_id": "s1",
        },
    )
    assert result["status"] == "failed"
