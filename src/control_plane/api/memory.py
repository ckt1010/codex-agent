from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from common.models import MemoryRecord

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/index")
def list_memory_index() -> dict[str, Any]:
    records = router.memory.query_fresh()
    return {"records": [r.model_dump() for r in records]}


@router.post("/index")
def upsert_memory(record: MemoryRecord) -> dict[str, Any]:
    try:
        router.memory.save(record)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "saved", "memory_id": record.memory_id}


@router.get("/content")
def get_memory_content(oss_uri: str) -> dict[str, Any]:
    if not oss_uri:
        raise HTTPException(status_code=400, detail="oss_uri is required")
    try:
        content = router.oss.get_text(oss_uri)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"oss_uri": oss_uri, "content": content}
