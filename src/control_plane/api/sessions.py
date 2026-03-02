from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter

from common.models import SessionSummary

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_sessions_markdown(agents: list[dict[str, Any]], sessions: list[SessionSummary]) -> str:
    by_agent: dict[str, list[SessionSummary]] = defaultdict(list)
    for item in sessions:
        by_agent[item.agent_name].append(item)

    lines: list[str] = ["# Device Sessions", ""]
    if not agents:
        lines.append("No registered agents.")
        return "\n".join(lines)

    for agent in agents:
        name = str(agent.get("agent_name") or "unknown")
        status = str(agent.get("status") or "unknown")
        queue_len = int(agent.get("queue_len") or 0)
        lines.append(f"## `{name}`")
        lines.append(f"- status: `{status}`")
        lines.append(f"- queue_len: `{queue_len}`")
        lines.append("")
        lines.append("| Session ID | Last Event | Last Output | At |")
        lines.append("|---|---|---|---|")

        agent_sessions = by_agent.get(name, [])
        if not agent_sessions:
            lines.append("| _none_ | _none_ | _none_ | _none_ |")
            lines.append("")
            continue

        for session in agent_sessions:
            lines.append(
                f"| `{_escape_cell(session.session_id)}` | "
                f"`{_escape_cell(session.last_event_type)}` | "
                f"{_escape_cell(session.last_output)} | "
                f"`{_escape_cell(session.last_event_at)}` |"
            )
        lines.append("")

    lines.append(
        "Use command format: "
        "`@codex @agent:<name> @session:<session_id> @proj:<alias> <task>`"
    )
    return "\n".join(lines)


@router.get("/list")
def list_sessions() -> dict[str, Any]:
    repo = router.repo
    sessions = repo.list_session_summaries()
    return {"sessions": [item.model_dump() for item in sessions]}


@router.get("/markdown")
def list_sessions_markdown() -> dict[str, str]:
    repo = router.repo
    agents = repo.list_agents()
    sessions = repo.list_session_summaries()
    return {"markdown": render_sessions_markdown(agents, sessions)}
