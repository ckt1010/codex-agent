#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${CONTROL_PLANE_URL:-}" || -z "${AGENT_NAME:-}" ]]; then
  echo "CONTROL_PLANE_URL and AGENT_NAME are required"
  exit 1
fi

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
python - <<'PY'
from agent_ubuntu.runner import UbuntuAgentRunner
import os
import time

runner = UbuntuAgentRunner(os.environ["CONTROL_PLANE_URL"], os.environ["AGENT_NAME"])
interval = int(os.environ.get("POLL_INTERVAL", "5"))

while True:
    runner.heartbeat()
    runner.pull_once()
    time.sleep(interval)
PY
