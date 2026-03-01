from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from common.models import AgentDescriptor, Citation, MemoryRecord, RunEvent, TaskEnvelope


class SQLiteRepo:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        ddl = schema_path.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(ddl)
            conn.commit()

    def insert_bootstrap_code(self, code: str, expires_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                (
                    "INSERT OR REPLACE INTO "
                    "bootstrap_codes(code, expires_at, consumed_at, consumed_by_agent) "
                    "VALUES (?, ?, NULL, NULL)"
                ),
                (code, expires_at),
            )
            conn.commit()

    def get_bootstrap_code(self, code: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM bootstrap_codes WHERE code = ?", (code,)).fetchone()

    def consume_bootstrap_code(self, code: str, consumed_at: str, agent_name: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE bootstrap_codes
                SET consumed_at = ?, consumed_by_agent = ?
                WHERE code = ? AND consumed_at IS NULL
                """,
                (consumed_at, agent_name, code),
            )
            conn.commit()
            return cur.rowcount == 1

    def insert_agent_token(
        self, token: str, agent_name: str, expires_at: str, created_at: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                (
                    "INSERT INTO agent_tokens(token, agent_name, expires_at, created_at) "
                    "VALUES (?, ?, ?, ?)"
                ),
                (token, agent_name, expires_at, created_at),
            )
            conn.commit()

    def upsert_agent(self, agent: AgentDescriptor) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agents(
                  agent_name, agent_type, capabilities_json, status, queue_len, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_name) DO UPDATE SET
                  agent_type=excluded.agent_type,
                  capabilities_json=excluded.capabilities_json,
                  status=excluded.status,
                  queue_len=excluded.queue_len,
                  last_seen=excluded.last_seen
                """,
                (
                    agent.agent_name,
                    agent.agent_type,
                    json.dumps(agent.capabilities),
                    agent.status,
                    agent.queue_len,
                    agent.last_seen,
                ),
            )
            conn.commit()

    def get_agent(self, agent_name: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM agents WHERE agent_name = ?", (agent_name,)
            ).fetchone()

    def add_task_dedup(
        self, source: str, source_message_id: str, task_id: str, created_at: str
    ) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    (
                        "INSERT INTO task_dedup(source, source_message_id, task_id, created_at) "
                        "VALUES (?, ?, ?, ?)"
                    ),
                    (source, source_message_id, task_id, created_at),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def insert_task(self, task: TaskEnvelope, status: str = "queued") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks(
                  task_id, source, source_message_id, requester_id, target_agent,
                  project_alias, instruction, priority, created_at, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.source,
                    task.source_message_id,
                    task.requester_id,
                    task.target_agent,
                    task.project_alias,
                    task.instruction,
                    task.priority,
                    task.created_at,
                    status,
                ),
            )
            conn.commit()

    def pull_next_task_for_agent(self, agent_name: str, now_iso: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM tasks
                WHERE target_agent = ? AND status = 'queued'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (agent_name,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE tasks SET status='in_progress', assigned_at=? WHERE task_id=?",
                (now_iso, row["task_id"]),
            )
            conn.commit()
            return dict(row)

    def insert_event(self, event: RunEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                (
                    "INSERT INTO run_events(task_id, agent_name, thread_id, "
                    "event_type, summary, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (
                    event.task_id,
                    event.agent_name,
                    event.thread_id,
                    event.event_type,
                    event.summary,
                    event.timestamp,
                ),
            )
            if event.event_type == "completed":
                conn.execute(
                    "UPDATE tasks SET status='completed', completed_at=? WHERE task_id=?",
                    (event.timestamp, event.task_id),
                )
            elif event.event_type == "tool_error":
                conn.execute(
                    "UPDATE tasks SET status='error', last_error=? WHERE task_id=?",
                    (event.summary, event.task_id),
                )
            conn.commit()

    def insert_memory(self, mem: MemoryRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_records(
                  memory_id, source_type, source_doc_id, source_version, oss_uri, visibility, owner,
                  summary, conclusions, key_pages_json, evidence_snippets_json, citations_json,
                  extracted_at, extracted_by_agent, ttl_seconds, fresh_until, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem.memory_id,
                    mem.source_type,
                    mem.source_doc_id,
                    mem.source_version,
                    mem.oss_uri,
                    mem.visibility,
                    mem.owner,
                    mem.summary,
                    mem.conclusions,
                    json.dumps(mem.key_pages),
                    json.dumps(mem.evidence_snippets),
                    json.dumps([c.model_dump() for c in mem.citations]),
                    mem.extracted_at,
                    mem.extracted_by_agent,
                    mem.ttl_seconds,
                    mem.fresh_until,
                    mem.status,
                ),
            )
            conn.commit()

    def list_fresh_memory(self, now_iso: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                (
                    "SELECT * FROM memory_records "
                    "WHERE status='fresh' AND fresh_until > ? "
                    "ORDER BY extracted_at DESC"
                ),
                (now_iso,),
            ).fetchall()
        out: list[MemoryRecord] = []
        for row in rows:
            citations = [Citation(**item) for item in json.loads(row["citations_json"])]
            out.append(
                MemoryRecord(
                    memory_id=row["memory_id"],
                    source_type=row["source_type"],
                    source_doc_id=row["source_doc_id"],
                    source_version=row["source_version"],
                    oss_uri=row["oss_uri"],
                    visibility=row["visibility"],
                    owner=row["owner"],
                    summary=row["summary"],
                    conclusions=row["conclusions"],
                    key_pages=json.loads(row["key_pages_json"]),
                    evidence_snippets=json.loads(row["evidence_snippets_json"]),
                    citations=citations,
                    extracted_at=row["extracted_at"],
                    extracted_by_agent=row["extracted_by_agent"],
                    ttl_seconds=row["ttl_seconds"],
                    fresh_until=row["fresh_until"],
                    status=row["status"],
                )
            )
        return out
