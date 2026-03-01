from __future__ import annotations

import httpx

from common.timeutil import utcnow_iso


class MacAgentRunner:
    def __init__(self, base_url: str, agent_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name

    def heartbeat(self, queue_len: int = 0) -> dict:
        payload = {
            "agent_name": self.agent_name,
            "queue_len": queue_len,
            "status": "online",
            "capabilities": ["codex_app_reader"],
        }
        r = httpx.post(f"{self.base_url}/api/agents/heartbeat", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def pull_once(self) -> dict:
        r = httpx.post(
            f"{self.base_url}/api/agents/pull-task",
            json={"agent_name": self.agent_name},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        task = data.get("task")
        if not task:
            return {"status": "idle"}

        event = {
            "task_id": task["task_id"],
            "agent_name": self.agent_name,
            "thread_id": f"thread-{task['task_id']}",
            "event_type": "completed",
            "summary": "mock mac execution completed",
            "timestamp": utcnow_iso(),
        }
        e = httpx.post(f"{self.base_url}/api/events/run", json=event, timeout=10)
        e.raise_for_status()
        return {"status": "completed", "task_id": task["task_id"]}
