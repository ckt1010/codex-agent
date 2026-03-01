from __future__ import annotations

import httpx


class MockFeishuConnector:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def ingest(self, payload: dict) -> dict:
        r = httpx.post(f"{self.base_url}/api/tasks/ingest", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
