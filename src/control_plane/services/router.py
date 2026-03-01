from __future__ import annotations

from common.errors import ValidationError


def route_task(target_agent: str | None, agent_online: bool) -> str:
    if not target_agent:
        raise ValidationError(code="missing_target_agent", message="target_agent is required")
    if not agent_online:
        raise ValidationError(code="agent_offline", message=f"agent '{target_agent}' is offline")
    return target_agent
