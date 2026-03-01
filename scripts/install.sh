#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ROLE=""
AGENT_NAME=""
BOOTSTRAP_CODE=""
PROJECT_MAP=""
CONTROL_PLANE_URL="${CONTROL_PLANE_URL:-http://127.0.0.1:8000}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role)
      ROLE="$2"
      shift 2
      ;;
    --agent-name)
      AGENT_NAME="$2"
      shift 2
      ;;
    --bootstrap-code)
      BOOTSTRAP_CODE="$2"
      shift 2
      ;;
    --project-map)
      PROJECT_MAP="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$ROLE" ]]; then
  echo "Usage: install.sh --role control-plane|agent-mac|agent-ubuntu [--agent-name NAME] [--bootstrap-code CODE] [--project-map PATH]"
  exit 1
fi

mkdir -p .runtime data/oss

register_agent() {
  local agent_type="$1"
  if [[ -z "$AGENT_NAME" || -z "$BOOTSTRAP_CODE" ]]; then
    echo "--agent-name and --bootstrap-code are required for $ROLE"
    exit 1
  fi

  local resp
  resp="$(curl -sS -X POST "${CONTROL_PLANE_URL}/api/agents/register" \
    -H 'content-type: application/json' \
    -d "{\"agent_name\":\"${AGENT_NAME}\",\"agent_type\":\"${agent_type}\",\"bootstrap_code\":\"${BOOTSTRAP_CODE}\"}")"

  local token expires_at
  token="$(printf '%s' "$resp" | python -c 'import json,sys; print(json.load(sys.stdin).get("agent_token",""))')"
  expires_at="$(printf '%s' "$resp" | python -c 'import json,sys; print(json.load(sys.stdin).get("expires_at",""))')"

  if [[ -z "$token" ]]; then
    echo "Agent registration failed: $resp"
    exit 1
  fi

  cat > ".runtime/${AGENT_NAME}.env" <<ENV
CONTROL_PLANE_URL=${CONTROL_PLANE_URL}
AGENT_NAME=${AGENT_NAME}
AGENT_TOKEN=${token}
AGENT_TOKEN_EXPIRES_AT=${expires_at}
PROJECT_MAP=${PROJECT_MAP}
ENV

  echo "registered ${AGENT_NAME}; env file: .runtime/${AGENT_NAME}.env"
}

case "$ROLE" in
  control-plane)
    cat > .runtime/control-plane.env <<ENV
CODEX_BRIDGE_DB_PATH=${ROOT_DIR}/data/control_plane.db
CODEX_BRIDGE_OSS_ROOT=${ROOT_DIR}/data/oss
ENV
    echo "control-plane initialized"
    echo "next: source .runtime/control-plane.env && ./scripts/run_control_plane.sh"
    ;;
  agent-mac)
    register_agent "mac_app"
    echo "next: source .runtime/${AGENT_NAME}.env && ./scripts/run_agent_mac.sh"
    ;;
  agent-ubuntu)
    register_agent "ubuntu_cli"
    cat > .runtime/${AGENT_NAME}.docker-compose.yml <<YAML
services:
  codex-agent-runner:
    image: python:3.12-slim
    working_dir: /app
    command: ["bash", "-lc", "./scripts/run_agent_ubuntu.sh"]
    environment:
      - CONTROL_PLANE_URL=${CONTROL_PLANE_URL}
      - AGENT_NAME=${AGENT_NAME}
    volumes:
      - ${ROOT_DIR}:/app
      - /workspace:/workspace
      - /var/lib/codex-agent:/var/lib/codex-agent
      - /root/.codex:/root/.codex
YAML
    echo "docker compose stub: .runtime/${AGENT_NAME}.docker-compose.yml"
    ;;
  *)
    echo "Unsupported role: $ROLE"
    exit 1
    ;;
esac
