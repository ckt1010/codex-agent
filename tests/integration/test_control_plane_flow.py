from __future__ import annotations


def _new_bootstrap(client):
    res = client.post("/api/bootstrap/new")
    assert res.status_code == 200
    return res.json()["bootstrap_code"]


def _register_agent(client, name: str, agent_type: str = "mac_app"):
    code = _new_bootstrap(client)
    res = client.post(
        "/api/agents/register",
        json={"agent_name": name, "agent_type": agent_type, "bootstrap_code": code},
    )
    assert res.status_code == 200
    assert res.json()["agent_token"]


def test_register_heartbeat_pull_event_completed(client) -> None:
    _register_agent(client, "mbp-work")

    hb = client.post(
        "/api/agents/heartbeat",
        json={"agent_name": "mbp-work", "queue_len": 0, "status": "online", "capabilities": ["x"]},
    )
    assert hb.status_code == 200

    ingest = client.post(
        "/api/tasks/ingest",
        json={
            "task_id": "task-1",
            "source": "feishu",
            "source_message_id": "m1",
            "requester_id": "u1",
            "target_agent": "mbp-work",
            "project_alias": "backend",
            "instruction": "fix bug",
            "priority": 1,
            "created_at": "2026-03-01T00:00:00+00:00",
        },
    )
    assert ingest.status_code == 200
    assert ingest.json()["status"] == "accepted"

    pulled = client.post("/api/agents/pull-task", json={"agent_name": "mbp-work"})
    assert pulled.status_code == 200
    task = pulled.json()["task"]
    assert task["task_id"] == "task-1"

    event = client.post(
        "/api/events/run",
        json={
            "task_id": "task-1",
            "agent_name": "mbp-work",
            "thread_id": "thread-task-1",
            "event_type": "completed",
            "summary": "done",
            "timestamp": "2026-03-01T00:10:00+00:00",
        },
    )
    assert event.status_code == 200

    pulled_again = client.post("/api/agents/pull-task", json={"agent_name": "mbp-work"})
    assert pulled_again.json()["task"] is None


def test_task_only_target_agent_can_pull(client) -> None:
    _register_agent(client, "mbp-work")
    _register_agent(client, "ubuntu-dev-1", agent_type="ubuntu_cli")

    ingest = client.post(
        "/api/tasks/ingest",
        json={
            "task_id": "task-2",
            "source": "imessage",
            "source_message_id": "m2",
            "requester_id": "u2",
            "target_agent": "ubuntu-dev-1",
            "project_alias": "backend",
            "instruction": "run test",
            "priority": 0,
            "created_at": "2026-03-01T00:00:00+00:00",
        },
    )
    assert ingest.status_code == 200

    wrong_pull = client.post("/api/agents/pull-task", json={"agent_name": "mbp-work"})
    assert wrong_pull.status_code == 200
    assert wrong_pull.json()["task"] is None

    right_pull = client.post("/api/agents/pull-task", json={"agent_name": "ubuntu-dev-1"})
    assert right_pull.status_code == 200
    assert right_pull.json()["task"]["task_id"] == "task-2"
