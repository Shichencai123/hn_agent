"""SSE 流式响应单元测试。"""

from __future__ import annotations

import json

import pytest

from hn_agent.agents.streaming import SSEEvent, VALID_EVENT_TYPES


# ── SSEEvent 测试 ────────────────────────────────────────


class TestSSEEvent:
    def test_valid_event_types(self):
        for event_type in VALID_EVENT_TYPES:
            event = SSEEvent(event=event_type, data={"key": "value"})
            assert event.event == event_type

    def test_invalid_event_type_raises(self):
        with pytest.raises(ValueError, match="无效的 SSE 事件类型"):
            SSEEvent(event="invalid_type")

    def test_default_data_is_empty_dict(self):
        event = SSEEvent(event="token")
        assert event.data == {}

    def test_to_sse_string_format(self):
        event = SSEEvent(event="token", data={"content": "hello"})
        result = event.to_sse_string()
        assert result.startswith("event: token\n")
        assert "data: " in result
        assert result.endswith("\n\n")
        # 解析 data 行
        data_line = result.split("\n")[1]
        data_json = data_line[len("data: "):]
        parsed = json.loads(data_json)
        assert parsed == {"content": "hello"}

    def test_to_sse_string_unicode(self):
        event = SSEEvent(event="token", data={"content": "你好世界"})
        result = event.to_sse_string()
        assert "你好世界" in result

    def test_to_dict(self):
        event = SSEEvent(event="tool_call", data={"tool_name": "bash"})
        d = event.to_dict()
        assert d == {"event": "tool_call", "data": {"tool_name": "bash"}}

    def test_done_event(self):
        event = SSEEvent(event="done", data={"finished": True})
        assert event.event == "done"
        assert event.data["finished"] is True

    def test_tool_result_event(self):
        event = SSEEvent(
            event="tool_result",
            data={"tool_name": "bash", "output": "hello world"},
        )
        assert event.event == "tool_result"

    def test_subagent_events(self):
        start = SSEEvent(event="subagent_start", data={"agent": "bash_agent"})
        result = SSEEvent(event="subagent_result", data={"output": "done"})
        assert start.event == "subagent_start"
        assert result.event == "subagent_result"


class TestValidEventTypes:
    def test_all_expected_types_present(self):
        expected = {"token", "tool_call", "tool_result", "subagent_start", "subagent_result", "done"}
        assert VALID_EVENT_TYPES == expected

    def test_frozen_set_immutable(self):
        with pytest.raises(AttributeError):
            VALID_EVENT_TYPES.add("new_type")
