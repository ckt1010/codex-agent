from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from common.models import RunEvent

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/run")
def run_event(event: RunEvent) -> dict[str, Any]:
    router.repo.insert_event(event)
    return {"status": "recorded"}
