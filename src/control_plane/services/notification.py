from __future__ import annotations

from typing import Any

import httpx


class NotificationFanout:
    def __init__(
        self,
        feishu_push_url: str = "",
        imessage_push_url: str = "",
        timeout_seconds: int = 10,
    ) -> None:
        self.targets = {
            "feishu": feishu_push_url.strip(),
            "imessage": imessage_push_url.strip(),
        }
        self.timeout_seconds = timeout_seconds

    def _target_for_source(self, source: str) -> str:
        return self.targets.get(source, "")

    @staticmethod
    def _build_markdown(task: dict[str, Any], event: dict[str, Any]) -> str:
        session_id = str(task.get("session_id") or event.get("thread_id") or "new")
        return (
            "### Task Update\n"
            f"- task_id: `{task.get('task_id')}`\n"
            f"- agent: `{event.get('agent_name')}`\n"
            f"- event: `{event.get('event_type')}`\n"
            f"- session: `{session_id}`\n"
            f"- project: `{task.get('project_alias')}`\n"
            f"- at: `{event.get('timestamp')}`\n\n"
            f"**Summary**\n{event.get('summary') or ''}"
        )

    def notify_task_event(self, task: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        source = str(task.get("source") or "")
        target_url = self._target_for_source(source)
        if not target_url:
            return {"status": "skipped", "reason": "push_url_not_configured", "source": source}

        payload = {
            "source": source,
            "requester_id": str(task.get("requester_id") or ""),
            "task_id": str(task.get("task_id") or ""),
            "event_type": str(event.get("event_type") or ""),
            "markdown": self._build_markdown(task, event),
        }
        response = httpx.post(target_url, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        return {"status": "sent", "source": source, "target_url": target_url}
