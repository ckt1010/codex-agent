from __future__ import annotations

import httpx

from agent_ubuntu.codex_exec import run_codex_instruction
from common.timeutil import utcnow_iso


class UbuntuAgentRunner:
    def __init__(self, base_url: str, agent_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name

    def heartbeat(self, queue_len: int = 0) -> dict:
        payload = {
            "agent_name": self.agent_name,
            "queue_len": queue_len,
            "status": "online",
            "capabilities": ["codex_cli_runner"],
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

        summary = run_codex_instruction(task["instruction"])
        event = {
            "task_id": task["task_id"],
            "agent_name": self.agent_name,
            "thread_id": task.get("session_id") or f"thread-{task['task_id']}",
            "event_type": "completed",
            "summary": summary,
            "timestamp": utcnow_iso(),
        }
        e = httpx.post(f"{self.base_url}/api/events/run", json=event, timeout=10)
        e.raise_for_status()
        return {"status": "completed", "task_id": task["task_id"]}
