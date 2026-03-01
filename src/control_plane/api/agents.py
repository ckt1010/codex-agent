from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from common.models import AgentDescriptor, AgentType
from common.timeutil import utcnow_iso

router = APIRouter(prefix="/api/agents", tags=["agents"])


class RegisterRequest(BaseModel):
    agent_name: str
    agent_type: str
    bootstrap_code: str


class HeartbeatRequest(BaseModel):
    agent_name: str
    queue_len: int = 0
    status: str = "online"
    capabilities: list[str] = Field(default_factory=list)


class PullRequest(BaseModel):
    agent_name: str


def _normalize_agent_type(agent_type: str) -> AgentType:
    if agent_type not in {"mac_app", "ubuntu_cli"}:
        raise HTTPException(status_code=400, detail=f"invalid agent_type: {agent_type}")
    return cast(AgentType, agent_type)


@router.post("/register")
def register_agent(req: RegisterRequest) -> dict[str, Any]:
    repo = router.repo
    bootstrap = router.bootstrap

    try:
        token, expires_at = bootstrap.consume_code(req.bootstrap_code, req.agent_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    descriptor = AgentDescriptor(
        agent_name=req.agent_name,
        agent_type=_normalize_agent_type(req.agent_type),
        capabilities=[],
        status="online",
        queue_len=0,
        last_seen=utcnow_iso(),
    )
    repo.upsert_agent(descriptor)
    return {"agent_token": token, "expires_at": expires_at}


@router.post("/heartbeat")
def heartbeat(req: HeartbeatRequest) -> dict[str, Any]:
    existing = router.repo.get_agent(req.agent_name)
    existing_type = existing["agent_type"] if existing is not None else "mac_app"
    agent_type = _normalize_agent_type(existing_type)
    descriptor = AgentDescriptor(
        agent_name=req.agent_name,
        agent_type=agent_type,
        capabilities=req.capabilities,
        status=req.status,
        queue_len=req.queue_len,
        last_seen=utcnow_iso(),
    )
    router.repo.upsert_agent(descriptor)
    return {"status": "ok"}


@router.post("/pull-task")
def pull_task(req: PullRequest) -> dict[str, Any]:
    task = router.repo.pull_next_task_for_agent(req.agent_name, utcnow_iso())
    if task is None:
        return {"task": None}
    return {"task": task}
