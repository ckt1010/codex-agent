from __future__ import annotations

from connectors.bluebubbles_bridge import BlueBubblesBridge
from connectors.command_bridge import CommandBridge


def test_parse_command_success() -> None:
    cmd = CommandBridge.parse_command("@codex @agent:mbp-work @proj:backend 修复支付重试")
    assert cmd is not None
    assert cmd.target_agent == "mbp-work"
    assert cmd.project_alias == "backend"
    assert cmd.instruction == "修复支付重试"


def test_parse_command_requires_full_format() -> None:
    cmd = CommandBridge.parse_command("hello world")
    assert cmd is None


def test_parse_command_with_session() -> None:
    cmd = CommandBridge.parse_command(
        "@codex @agent:mbp-work @session:s-123 @proj:backend 修复支付重试"
    )
    assert cmd is not None
    assert cmd.session_id == "s-123"


def test_payload_extract_compatible_shapes() -> None:
    payload = {
        "data": {
            "guid": "g1",
            "text": "@codex @agent:mbp @proj:p t",
            "handle": {"address": "+8613800000000"},
        }
    }
    assert BlueBubblesBridge._extract_sender(payload) == "+8613800000000"
    assert BlueBubblesBridge._extract_text(payload) == "@codex @agent:mbp @proj:p t"
    assert BlueBubblesBridge._extract_source_message_id(payload) == "g1"
