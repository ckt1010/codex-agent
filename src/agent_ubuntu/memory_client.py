from __future__ import annotations

import httpx


class MemoryClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def list_fresh(self) -> dict:
        resp = httpx.get(f"{self.base_url}/api/memory/index", timeout=10)
        resp.raise_for_status()
        return resp.json()
