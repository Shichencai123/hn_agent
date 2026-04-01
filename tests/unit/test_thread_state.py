"""线程状态单元测试。"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from hn_agent.agents.thread_state import (
    Artifact,
    ImageData,
    ThreadState,
    artifacts_reducer,
    thread_state_from_json,
    thread_state_to_json,
)


# ── Artifact 数据模型 ────────────────────────────────────


class TestArtifact:
    def test_create_with_defaults(self):
        a = Artifact(id="a1", type="code", title="Hello", content="print('hi')")
        assert a.id == "a1"
        assert a.type == "code"
        assert isinstance(a.created_at, datetime)

    def test_to_dict_and_from_dict_roundtrip(self):
        ts = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        a = Artifact(id="a1", type="doc", title="Doc", content="# Title", created_at=ts)
        d = a.to_dict()
        restored = Artifact.from_dict(d)
        assert restored.id == a.id
        assert restored.type == a.type
        assert restored.title == a.title
        assert restored.content == a.content
        assert restored.created_at == a.created_at

    def test_from_dict_missing_created_at(self):
        d = {"id": "x", "type": "code", "title": "T", "content": "C"}
        a = Artifact.from_dict(d)
        assert isinstance(a.created_at, datetime)


# ── ImageData 数据模型 ───────────────────────────────────


class TestImageData:
    def test_create_without_data(self):
        img = ImageData(id="i1", url="https://example.com/img.png", alt_text="test")
        assert img.data is None

    def test_create_with_data(self):
        img = ImageData(id="i1", url="https://example.com/img.png", alt_text="test", data=b"\x89PNG")
        assert img.data == b"\x89PNG"

    def test_to_dict_and_from_dict_roundtrip_with_data(self):
        img = ImageData(id="i1", url="https://img.com/a.png", alt_text="pic", data=b"\x00\x01\x02\xff")
        d = img.to_dict()
        restored = ImageData.from_dict(d)
        assert restored.id == img.id
        assert restored.url == img.url
        assert restored.alt_text == img.alt_text
        assert restored.data == img.data

    def test_to_dict_and_from_dict_roundtrip_without_data(self):
        img = ImageData(id="i2", url="https://img.com/b.png", alt_text="no data")
        d = img.to_dict()
        restored = ImageData.from_dict(d)
        assert restored.data is None

    def test_to_dict_data_is_base64_string(self):
        img = ImageData(id="i1", url="u", alt_text="a", data=b"hello")
        d = img.to_dict()
        assert isinstance(d["data"], str)


# ── artifacts_reducer ────────────────────────────────────


class TestArtifactsReducer:
    def test_append_new(self):
        existing = [Artifact(id="a1", type="code", title="A", content="1")]
        new = [Artifact(id="a2", type="doc", title="B", content="2")]
        result = artifacts_reducer(existing, new)
        assert len(result) == 2
        assert result[0].id == "a1"
        assert result[1].id == "a2"

    def test_update_existing_by_id(self):
        existing = [
            Artifact(id="a1", type="code", title="Old", content="old"),
            Artifact(id="a2", type="doc", title="Keep", content="keep"),
        ]
        new = [Artifact(id="a1", type="code", title="New", content="new")]
        result = artifacts_reducer(existing, new)
        assert len(result) == 2
        assert result[0].title == "New"
        assert result[0].content == "new"
        assert result[1].id == "a2"

    def test_mixed_append_and_update(self):
        existing = [Artifact(id="a1", type="code", title="A", content="1")]
        new = [
            Artifact(id="a1", type="code", title="A-updated", content="1u"),
            Artifact(id="a3", type="doc", title="C", content="3"),
        ]
        result = artifacts_reducer(existing, new)
        assert len(result) == 2
        assert result[0].title == "A-updated"
        assert result[1].id == "a3"

    def test_empty_existing(self):
        result = artifacts_reducer([], [Artifact(id="a1", type="t", title="T", content="C")])
        assert len(result) == 1

    def test_empty_new(self):
        existing = [Artifact(id="a1", type="t", title="T", content="C")]
        result = artifacts_reducer(existing, [])
        assert len(result) == 1

    def test_both_empty(self):
        assert artifacts_reducer([], []) == []

    def test_does_not_mutate_existing(self):
        existing = [Artifact(id="a1", type="t", title="T", content="C")]
        original_len = len(existing)
        artifacts_reducer(existing, [Artifact(id="a2", type="t", title="T2", content="C2")])
        assert len(existing) == original_len


# ── images reducer (operator.add) ───────────────────────


class TestImagesReducer:
    def test_append_via_operator_add(self):
        """images 使用 operator.add，即列表拼接。"""
        existing = [ImageData(id="i1", url="u1", alt_text="a1")]
        new = [ImageData(id="i2", url="u2", alt_text="a2")]
        import operator
        result = operator.add(existing, new)
        assert len(result) == 2
        assert result[0].id == "i1"
        assert result[1].id == "i2"


# ── ThreadState Schema ──────────────────────────────────


class TestThreadState:
    def test_schema_has_expected_fields(self):
        annotations = ThreadState.__annotations__
        assert "artifacts" in annotations
        assert "images" in annotations
        assert "title" in annotations
        assert "thread_data" in annotations


# ── JSON 序列化 / 反序列化 ────────────────────────────────


class TestThreadStateSerialization:
    def _make_state(self) -> dict:
        return {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
            ],
            "artifacts": [
                Artifact(
                    id="a1",
                    type="code",
                    title="Script",
                    content="print('hi')",
                    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                ),
            ],
            "images": [
                ImageData(id="i1", url="https://img.com/x.png", alt_text="pic", data=b"\x89PNG"),
            ],
            "title": "Test Thread",
            "thread_data": {"key": "value", "nested": {"a": 1}},
        }

    def test_roundtrip(self):
        state = self._make_state()
        json_str = thread_state_to_json(state)
        restored = thread_state_from_json(json_str)

        # messages
        assert len(restored["messages"]) == 2
        assert isinstance(restored["messages"][0], HumanMessage)
        assert restored["messages"][0].content == "Hello"
        assert isinstance(restored["messages"][1], AIMessage)
        assert restored["messages"][1].content == "Hi there!"

        # artifacts
        assert len(restored["artifacts"]) == 1
        a = restored["artifacts"][0]
        assert a.id == "a1"
        assert a.content == "print('hi')"
        assert a.created_at == datetime(2025, 1, 1, tzinfo=timezone.utc)

        # images
        assert len(restored["images"]) == 1
        img = restored["images"][0]
        assert img.id == "i1"
        assert img.data == b"\x89PNG"

        # title & thread_data
        assert restored["title"] == "Test Thread"
        assert restored["thread_data"] == {"key": "value", "nested": {"a": 1}}

    def test_json_is_valid_json(self):
        state = self._make_state()
        json_str = thread_state_to_json(state)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_empty_state_roundtrip(self):
        state: dict = {
            "messages": [],
            "artifacts": [],
            "images": [],
            "title": None,
            "thread_data": {},
        }
        json_str = thread_state_to_json(state)
        restored = thread_state_from_json(json_str)
        assert restored["messages"] == []
        assert restored["artifacts"] == []
        assert restored["images"] == []
        assert restored["title"] is None
        assert restored["thread_data"] == {}

    def test_partial_state_serialization(self):
        """只包含部分字段也能正常序列化。"""
        state = {"messages": [HumanMessage(content="test")], "title": "partial"}
        json_str = thread_state_to_json(state)
        restored = thread_state_from_json(json_str)
        assert restored["title"] == "partial"
        assert len(restored["messages"]) == 1
        assert "artifacts" not in restored
        assert "images" not in restored

    def test_tool_message_roundtrip(self):
        state = {
            "messages": [
                ToolMessage(content="result", tool_call_id="tc1"),
            ],
            "artifacts": [],
            "images": [],
            "title": None,
            "thread_data": {},
        }
        json_str = thread_state_to_json(state)
        restored = thread_state_from_json(json_str)
        assert len(restored["messages"]) == 1
        assert isinstance(restored["messages"][0], ToolMessage)
        assert restored["messages"][0].content == "result"

    def test_system_message_roundtrip(self):
        state = {
            "messages": [SystemMessage(content="You are helpful.")],
            "artifacts": [],
            "images": [],
            "title": None,
            "thread_data": {},
        }
        json_str = thread_state_to_json(state)
        restored = thread_state_from_json(json_str)
        assert isinstance(restored["messages"][0], SystemMessage)
