#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${CONTROL_PLANE_URL:-http://127.0.0.1:8000}"

bootstrap_code="$(curl -sS -X POST "${BASE_URL}/api/bootstrap/new" | python -c 'import sys,json; print(json.load(sys.stdin)["bootstrap_code"])')"

curl -sS -X POST "${BASE_URL}/api/agents/register" \
  -H 'content-type: application/json' \
  -d "{\"agent_name\":\"mbp-work\",\"agent_type\":\"mac_app\",\"bootstrap_code\":\"${bootstrap_code}\"}" >/dev/null

curl -sS -X POST "${BASE_URL}/api/agents/heartbeat" \
  -H 'content-type: application/json' \
  -d '{"agent_name":"mbp-work","queue_len":0,"status":"online","capabilities":["codex_app_reader"]}' >/dev/null

curl -sS -X POST "${BASE_URL}/api/tasks/ingest" \
  -H 'content-type: application/json' \
  -d '{"task_id":"demo-task-1","source":"feishu","source_message_id":"msg-demo-1","requester_id":"demo-user","target_agent":"mbp-work","project_alias":"demo","instruction":"echo demo","priority":1,"created_at":"2026-03-01T00:00:00+00:00"}'
