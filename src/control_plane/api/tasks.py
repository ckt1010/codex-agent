from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from common.models import TaskEnvelope
from control_plane.services.router import route_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/ingest")
def ingest_task(task: TaskEnvelope) -> dict[str, Any]:
    repo = router.repo
    dedupe = router.dedupe

    is_new = dedupe.register(task.source, task.source_message_id, task.task_id, task.created_at)
    if not is_new:
        return {"status": "duplicate", "task_id": task.task_id}

    agent = repo.get_agent(task.target_agent)
    try:
        route_task(
            task.target_agent, agent_online=agent is not None and agent["status"] == "online"
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo.insert_task(task)
    return {"status": "accepted", "task_id": task.task_id}
