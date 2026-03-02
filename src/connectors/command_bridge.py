from __future__ import annotations

import re
import uuid
from typing import Any

import httpx
from pydantic import BaseModel

from common.timeutil import utcnow_iso

COMMAND_RE = re.compile(
    r"@codex\s+@agent:(?P<agent>\S+)\s+(?:@session:(?P<session>\S+)\s+)?@proj:(?P<proj>\S+)\s+(?P<task>.+)",
    re.IGNORECASE,
)


class ParsedCommand(BaseModel):
    target_agent: str
    project_alias: str
    instruction: str
    session_id: str | None = None


class CommandBridge:
    def __init__(self, control_plane_url: str, source: str, outbound_push_url: str = "") -> None:
        self.control_plane_url = control_plane_url.rstrip("/")
        self.source = source
        self.outbound_push_url = outbound_push_url.strip()

    @staticmethod
    def parse_command(text: str) -> ParsedCommand | None:
        match = COMMAND_RE.search(text.strip())
        if not match:
            return None
        return ParsedCommand(
            target_agent=match.group("agent"),
            project_alias=match.group("proj"),
            instruction=match.group("task").strip(),
            session_id=match.group("session") or None,
        )

    @staticmethod
    def is_list_command(text: str) -> bool:
        return text.strip().lower() == "list"

    def get_sessions_markdown(self) -> str:
        response = httpx.get(f"{self.control_plane_url}/api/sessions/markdown", timeout=10)
        response.raise_for_status()
        return str(response.json().get("markdown") or "")

    def check_control_plane_health(self) -> tuple[bool, str]:
        try:
            response = httpx.get(f"{self.control_plane_url}/healthz", timeout=5)
            response.raise_for_status()
            status = str(response.json().get("status") or "")
            if status == "ok":
                return True, "control-plane reachable"
            response_text = getattr(response, "text", "")
            return False, f"unexpected healthz payload: {response_text}"
        except httpx.HTTPError as exc:
            return False, str(exc)

    def push_markdown(self, recipient: str, markdown: str) -> dict[str, Any]:
        if not self.outbound_push_url:
            return {"status": "skipped", "reason": "outbound_push_url_not_configured"}
        payload = {
            "source": self.source,
            "recipient": recipient,
            "markdown": markdown,
        }
        response = httpx.post(self.outbound_push_url, json=payload, timeout=10)
        response.raise_for_status()
        return {"status": "sent", "target": self.outbound_push_url}

    def ingest_to_control_plane(
        self, sender: str, source_message_id: str, command: ParsedCommand
    ) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "source": self.source,
            "source_message_id": source_message_id,
            "requester_id": sender or f"{self.source}-user",
            "target_agent": command.target_agent,
            "project_alias": command.project_alias,
            "instruction": command.instruction,
            "session_id": command.session_id,
            "priority": 0,
            "created_at": utcnow_iso(),
        }
        response = httpx.post(
            f"{self.control_plane_url}/api/tasks/ingest", json=payload, timeout=10
        )
        response.raise_for_status()
        return {
            "task_id": task_id,
            "control_plane": response.json(),
            "session_id": command.session_id,
        }
