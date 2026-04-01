"""嵌入式客户端单元测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hn_agent.client import ChatResponse, HarnessClient, ThreadInfo


# ── ChatResponse 测试 ────────────────────────────────────


class TestChatResponse:
    def test_basic_creation(self):
        resp = ChatResponse(thread_id="t1", content="hello")
        assert resp.thread_id == "t1"
        assert resp.content == "hello"
        assert resp.artifacts == []
        assert resp.token_usage == {}

    def test_with_artifacts(self):
        resp = ChatResponse(
            thread_id="t1",
            content="done",
            artifacts=[{"id": "a1", "type": "code"}],
            token_usage={"prompt": 100, "completion": 50},
        )
        assert len(resp.artifacts) == 1
        assert resp.token_usage["prompt"] == 100


# ── ThreadInfo 测试 ──────────────────────────────────────


class TestThreadInfo:
    def test_basic_creation(self):
        info = ThreadInfo(thread_id="t1")
        assert info.thread_id == "t1"
        assert info.title is None
        assert info.message_count == 0
        assert isinstance(info.created_at, datetime)

    def test_with_title(self):
        info = ThreadInfo(thread_id="t1", title="测试对话")
        assert info.title == "测试对话"


# ── HarnessClient 测试 ───────────────────────────────────


class TestHarnessClient:
    def test_init_defaults(self):
        client = HarnessClient()
        assert client._config_path is None
        assert client._agent_config_override == {}
        assert client._threads == {}
        assert client._agent is None

    def test_init_with_config_path(self):
        client = HarnessClient(config_path="/path/to/config.yaml")
        assert client._config_path == "/path/to/config.yaml"

    def test_init_with_agent_config(self):
        client = HarnessClient(agent_config={"model_name": "claude-3-opus"})
        assert client._agent_config_override["model_name"] == "claude-3-opus"

    def test_ensure_thread_creates_new(self):
        client = HarnessClient()
        info = client._ensure_thread("t1")
        assert info.thread_id == "t1"
        assert "t1" in client._threads

    def test_ensure_thread_returns_existing(self):
        client = HarnessClient()
        info1 = client._ensure_thread("t1")
        info2 = client._ensure_thread("t1")
        assert info1 is info2

    @pytest.mark.asyncio
    async def test_get_thread_not_found(self):
        client = HarnessClient()
        with pytest.raises(KeyError, match="线程不存在"):
            await client.get_thread("nonexistent")

    @pytest.mark.asyncio
    async def test_get_thread_found(self):
        client = HarnessClient()
        client._ensure_thread("t1")
        info = await client.get_thread("t1")
        assert info.thread_id == "t1"

    @pytest.mark.asyncio
    async def test_list_threads_empty(self):
        client = HarnessClient()
        threads = await client.list_threads()
        assert threads == []

    @pytest.mark.asyncio
    async def test_list_threads_sorted_by_created_at(self):
        client = HarnessClient()
        t1 = client._ensure_thread("t1")
        t1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t2 = client._ensure_thread("t2")
        t2.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
        t3 = client._ensure_thread("t3")
        t3.created_at = datetime(2023, 12, 31, tzinfo=timezone.utc)

        threads = await client.list_threads()
        assert [t.thread_id for t in threads] == ["t3", "t1", "t2"]

    @pytest.mark.asyncio
    async def test_list_threads_multiple(self):
        client = HarnessClient()
        client._ensure_thread("a")
        client._ensure_thread("b")
        threads = await client.list_threads()
        assert len(threads) == 2
