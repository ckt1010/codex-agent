from __future__ import annotations

import httpx

from connectors.command_bridge import CommandBridge


class _Resp:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_is_list_command() -> None:
    assert CommandBridge.is_list_command("list") is True
    assert CommandBridge.is_list_command(" LIST ") is True
    assert CommandBridge.is_list_command("@codex ...") is False


def test_get_sessions_markdown(monkeypatch) -> None:
    def fake_get(url: str, timeout: int = 10):
        _ = (url, timeout)
        return _Resp({"markdown": "# Device Sessions"})

    monkeypatch.setattr(httpx, "get", fake_get)
    bridge = CommandBridge("http://local", "imessage")
    assert bridge.get_sessions_markdown() == "# Device Sessions"


def test_push_markdown(monkeypatch) -> None:
    captured: list[tuple[str, dict]] = []

    def fake_post(url: str, json: dict | None = None, timeout: int = 10):
        _ = timeout
        captured.append((url, json or {}))
        return _Resp({"ok": True})

    monkeypatch.setattr(httpx, "post", fake_post)
    bridge = CommandBridge(
        "http://local",
        "imessage",
        outbound_push_url="http://push.local/imessage",
    )
    result = bridge.push_markdown("+8613", "### hello")
    assert result["status"] == "sent"
    assert captured == [
        (
            "http://push.local/imessage",
            {"source": "imessage", "recipient": "+8613", "markdown": "### hello"},
        )
    ]
