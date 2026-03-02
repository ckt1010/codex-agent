from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentType = Literal["mac_app", "ubuntu_cli"]
RunEventType = Literal["started", "tool_error", "completed"]
MemoryStatus = Literal["fresh", "stale", "superseded"]
Visibility = Literal["system", "human"]


class TaskEnvelope(BaseModel):
    task_id: str
    source: str
    source_message_id: str
    requester_id: str
    target_agent: str = Field(min_length=1)
    project_alias: str
    instruction: str
    session_id: str | None = None
    priority: int = 0
    created_at: str


class AgentDescriptor(BaseModel):
    agent_name: str
    agent_type: AgentType
    capabilities: list[str] = Field(default_factory=list)
    status: str
    queue_len: int = 0
    last_seen: str


class RunEvent(BaseModel):
    task_id: str
    agent_name: str
    thread_id: str
    event_type: RunEventType
    summary: str
    timestamp: str


class SessionSummary(BaseModel):
    agent_name: str
    session_id: str
    last_event_type: str
    last_output: str
    last_event_at: str


class Citation(BaseModel):
    source_doc_id: str
    page: int
    snippet_hash: str
    snippet_text: str
    locator: str


class MemoryRecord(BaseModel):
    memory_id: str
    source_type: str
    source_doc_id: str
    source_version: str
    oss_uri: str
    visibility: Visibility = "system"
    owner: str = "codex-bot"
    summary: str
    conclusions: str
    key_pages: list[int] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    extracted_at: str
    extracted_by_agent: str
    ttl_seconds: int
    fresh_until: str
    status: MemoryStatus
