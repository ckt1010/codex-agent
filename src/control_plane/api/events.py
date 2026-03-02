from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from common.models import RunEvent

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/run")
def run_event(event: RunEvent) -> dict[str, Any]:
    repo = router.repo
    repo.insert_event(event)
    task = repo.get_task(event.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"task not found: {event.task_id}")
    notify = router.notifier.notify_task_event(task=task, event=event.model_dump())
    return {"status": "recorded", "notify": notify}
