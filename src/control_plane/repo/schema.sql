PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS bootstrap_codes (
  code TEXT PRIMARY KEY,
  expires_at TEXT NOT NULL,
  consumed_at TEXT,
  consumed_by_agent TEXT
);

CREATE TABLE IF NOT EXISTS agent_tokens (
  token TEXT PRIMARY KEY,
  agent_name TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
  agent_name TEXT PRIMARY KEY,
  agent_type TEXT NOT NULL,
  capabilities_json TEXT NOT NULL,
  status TEXT NOT NULL,
  queue_len INTEGER NOT NULL DEFAULT 0,
  last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_dedup (
  source TEXT NOT NULL,
  source_message_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (source, source_message_id)
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  source_message_id TEXT NOT NULL,
  requester_id TEXT NOT NULL,
  target_agent TEXT NOT NULL,
  project_alias TEXT NOT NULL,
  instruction TEXT NOT NULL,
  session_id TEXT,
  priority INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,
  assigned_at TEXT,
  completed_at TEXT,
  last_error TEXT
);

CREATE TABLE IF NOT EXISTS run_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_agent_status_created
ON tasks(target_agent, status, created_at);

CREATE INDEX IF NOT EXISTS idx_run_events_agent_thread_time
ON run_events(agent_name, thread_id, timestamp);

CREATE TABLE IF NOT EXISTS memory_records (
  memory_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_doc_id TEXT NOT NULL,
  source_version TEXT NOT NULL,
  oss_uri TEXT,
  visibility TEXT NOT NULL,
  owner TEXT NOT NULL,
  summary TEXT NOT NULL,
  conclusions TEXT NOT NULL,
  key_pages_json TEXT NOT NULL,
  evidence_snippets_json TEXT NOT NULL,
  citations_json TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  extracted_by_agent TEXT NOT NULL,
  ttl_seconds INTEGER NOT NULL,
  fresh_until TEXT NOT NULL,
  status TEXT NOT NULL
);
