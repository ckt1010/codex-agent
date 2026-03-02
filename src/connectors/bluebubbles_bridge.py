from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

from connectors.command_bridge import CommandBridge


class BlueBubblesBridge:
    def __init__(self) -> None:
        control_plane_url = os.getenv("CONTROL_PLANE_URL", "http://127.0.0.1:8000")
        push_url = os.getenv("IMESSAGE_OUTBOUND_PUSH_URL", "")
        self.cmd = CommandBridge(
            control_plane_url=control_plane_url,
            source="imessage",
            outbound_push_url=push_url,
        )
        allowed = os.getenv("IMESSAGE_ALLOWED_SENDERS", "")
        self.allowed_senders = {x.strip() for x in allowed.split(",") if x.strip()}
        self.status_recipient = os.getenv("IMESSAGE_STATUS_RECIPIENT", "").strip()

    def notify_status(self, status: str, detail: str) -> dict[str, Any]:
        markdown = (
            "### System Status\n"
            "- component: `imessage-connector`\n"
            f"- status: `{status}`\n"
            f"- detail: {detail}"
        )
        recipient = self.status_recipient or "imessage-system"
        return self.cmd.push_markdown(recipient, markdown)

    @staticmethod
    def _extract_sender(payload: dict[str, Any]) -> str:
        # Compatible with different webhook shapes.
        return (
            str(payload.get("sender") or "")
            or str(payload.get("from") or "")
            or str(payload.get("address") or "")
            or str(((payload.get("data") or {}).get("handle") or {}).get("address") or "")
        )

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        return (
            str(payload.get("text") or "")
            or str(payload.get("message") or "")
            or str(payload.get("body") or "")
            or str((payload.get("data") or {}).get("text") or "")
            or str((payload.get("data") or {}).get("message") or "")
        )

    @staticmethod
    def _extract_source_message_id(payload: dict[str, Any]) -> str:
        return (
            str(payload.get("message_id") or "")
            or str(payload.get("guid") or "")
            or str((payload.get("data") or {}).get("guid") or "")
            or str(uuid.uuid4())
        )


bridge = BlueBubblesBridge()
app = FastAPI(title="BlueBubbles iMessage Bridge", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    bridge.notify_status("started", "imessage connector started")
    ok, detail = bridge.cmd.check_control_plane_health()
    if not ok:
        bridge.notify_status("control_plane_unreachable", detail)


@app.post("/webhooks/bluebubbles")
def webhook(payload: dict[str, Any]) -> dict[str, Any]:
    sender = bridge._extract_sender(payload)
    if bridge.allowed_senders and sender not in bridge.allowed_senders:
        return {"status": "ignored", "reason": "sender_not_allowed", "sender": sender}

    text = bridge._extract_text(payload)
    if bridge.cmd.is_list_command(text):
        try:
            markdown = bridge.cmd.get_sessions_markdown()
            pushed = bridge.cmd.push_markdown(sender, markdown)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"control-plane error: {exc}") from exc
        return {"status": "listed", "markdown": markdown, "push": pushed}

    cmd = bridge.cmd.parse_command(text)
    if cmd is None:
        return {
            "status": "ignored",
            "reason": "not_a_codex_command",
            "hint": "send `list` or @codex ...",
        }

    source_message_id = bridge._extract_source_message_id(payload)
    try:
        result = bridge.cmd.ingest_to_control_plane(sender, source_message_id, cmd)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"control-plane error: {exc}") from exc
    markdown = (
        f"### Task Accepted\n"
        f"- agent: `{cmd.target_agent}`\n"
        f"- session: `{cmd.session_id or 'new'}`\n"
        f"- project: `{cmd.project_alias}`\n"
        f"- task_id: `{result['task_id']}`"
    )
    pushed = bridge.cmd.push_markdown(sender, markdown)
    return {
        "status": "accepted",
        **result,
        "markdown": markdown,
        "push": pushed,
    }
