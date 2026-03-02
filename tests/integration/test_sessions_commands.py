from __future__ import annotations


def _new_bootstrap(client):
    return client.post("/api/bootstrap/new").json()["bootstrap_code"]


def _register_agent(client, agent_name: str, agent_type: str = "mac_app") -> None:
    code = _new_bootstrap(client)
    res = client.post(
        "/api/agents/register",
        json={"agent_name": agent_name, "agent_type": agent_type, "bootstrap_code": code},
    )
    assert res.status_code == 200


def test_sessions_markdown_and_list(client) -> None:
    _register_agent(client, "mbp-work")

    ingest = client.post(
        "/api/tasks/ingest",
        json={
            "task_id": "task-s1",
            "source": "imessage",
            "source_message_id": "m-s1",
            "requester_id": "u1",
            "target_agent": "mbp-work",
            "project_alias": "backend",
            "instruction": "continue fix",
            "session_id": "sess-123",
            "priority": 1,
            "created_at": "2026-03-02T00:00:00+00:00",
        },
    )
    assert ingest.status_code == 200

    pulled = client.post("/api/agents/pull-task", json={"agent_name": "mbp-work"})
    task = pulled.json()["task"]
    assert task["session_id"] == "sess-123"

    event = client.post(
        "/api/events/run",
        json={
            "task_id": "task-s1",
            "agent_name": "mbp-work",
            "thread_id": "sess-123",
            "event_type": "completed",
            "summary": "fixed and verified",
            "timestamp": "2026-03-02T00:05:00+00:00",
        },
    )
    assert event.status_code == 200

    listed = client.get("/api/sessions/list")
    assert listed.status_code == 200
    sessions = listed.json()["sessions"]
    assert any(s["agent_name"] == "mbp-work" and s["session_id"] == "sess-123" for s in sessions)

    markdown = client.get("/api/sessions/markdown")
    assert markdown.status_code == 200
    text = markdown.json()["markdown"]
    assert "# Device Sessions" in text
    assert "`mbp-work`" in text
    assert "`sess-123`" in text
    assert "fixed and verified" in text
