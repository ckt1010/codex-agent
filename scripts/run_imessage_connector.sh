#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${CONTROL_PLANE_URL:-}" ]]; then
  echo "CONTROL_PLANE_URL is required"
  exit 1
fi

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
exec uvicorn connectors.bluebubbles_bridge:app --host 0.0.0.0 --port "${IMESSAGE_CONNECTOR_PORT:-8090}"
