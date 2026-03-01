from __future__ import annotations

from pathlib import Path


def latest_session_paths(codex_home: str) -> list[str]:
    base = Path(codex_home).expanduser() / "sessions"
    if not base.exists():
        return []
    return sorted([str(p) for p in base.rglob("*.jsonl")])[-10:]
