from __future__ import annotations

from connectors.feishu_bridge import FeishuBridge


def test_extract_text_from_feishu_json_content() -> None:
    payload = {"event": {"message": {"content": '{"text":"list"}'}}}
    assert FeishuBridge._extract_text(payload) == "list"
