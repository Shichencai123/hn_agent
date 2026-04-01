"""记忆系统单元测试：MemoryUpdater, DebounceQueue, MemoryStorage, build_memory_prompt。"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from hn_agent.memory.prompt import MemoryChunk, build_memory_prompt
from hn_agent.memory.queue import DebounceQueue
from hn_agent.memory.storage import MemoryStorage
from hn_agent.memory.updater import MemoryUpdater


# ── 测试辅助 ──────────────────────────────────────────────


@dataclass
class FakeMessage:
    """模拟 BaseMessage 的测试替身。"""

    type: str
    content: str


@dataclass
class FakeLLMResponse:
    """模拟 LLM 响应。"""

    content: str


# ══════════════════════════════════════════════════════════
# MemoryUpdater 测试
# ══════════════════════════════════════════════════════════


class TestMemoryUpdater:
    """MemoryUpdater 单元测试。"""

    @pytest.mark.asyncio
    async def test_no_llm_returns_existing_memory(self):
        """无 LLM 时直接返回现有记忆。"""
        updater = MemoryUpdater(llm=None)
        messages = [FakeMessage(type="human", content="你好")]
        result = await updater.extract_and_update(messages, "已有记忆")
        assert result == "已有记忆"

    @pytest.mark.asyncio
    async def test_empty_messages_returns_existing(self):
        """空消息列表直接返回现有记忆。"""
        updater = MemoryUpdater(llm=None)
        result = await updater.extract_and_update([], "已有记忆")
        assert result == "已有记忆"

    @pytest.mark.asyncio
    async def test_with_llm_calls_ainvoke(self):
        """有 LLM 时调用 ainvoke 并返回结果。"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = FakeLLMResponse(content="更新后的记忆内容")

        updater = MemoryUpdater(llm=mock_llm)
        messages = [
            FakeMessage(type="human", content="我喜欢 Python"),
            FakeMessage(type="ai", content="好的，已记住"),
        ]
        result = await updater.extract_and_update(messages, "旧记忆")

        assert result == "更新后的记忆内容"
        mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_exception_preserves_existing(self):
        """LLM 调用异常时保留现有记忆。"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = RuntimeError("LLM 不可用")

        updater = MemoryUpdater(llm=mock_llm)
        messages = [FakeMessage(type="human", content="测试")]
        result = await updater.extract_and_update(messages, "安全记忆")

        assert result == "安全记忆"

    @pytest.mark.asyncio
    async def test_llm_returns_string(self):
        """LLM 返回纯字符串时也能正确处理。"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = "  纯字符串结果  "

        updater = MemoryUpdater(llm=mock_llm)
        messages = [FakeMessage(type="human", content="hello")]
        result = await updater.extract_and_update(messages, "")

        assert result == "纯字符串结果"

    def test_format_messages(self):
        """消息格式化为对话文本。"""
        messages = [
            FakeMessage(type="human", content="你好"),
            FakeMessage(type="ai", content="你好！"),
        ]
        text = MemoryUpdater._format_messages(messages)
        assert "[human]: 你好" in text
        assert "[ai]: 你好！" in text


# ══════════════════════════════════════════════════════════
# DebounceQueue 测试
# ══════════════════════════════════════════════════════════


class TestDebounceQueue:
    """DebounceQueue 单元测试。"""

    def test_submit_stores_pending(self):
        """提交后消息进入 pending 状态。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        msgs = [FakeMessage(type="human", content="hi")]
        queue.submit("t1", msgs)
        assert queue.has_pending("t1")
        assert queue.pending_count("t1") == 1

    def test_submit_empty_messages_ignored(self):
        """空消息列表不产生 pending。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        queue.submit("t1", [])
        assert not queue.has_pending("t1")

    def test_submit_merges_messages(self):
        """同一 thread_id 的多次提交合并消息。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        queue.submit("t1", [FakeMessage(type="human", content="a")])
        queue.submit("t1", [FakeMessage(type="human", content="b")])
        assert queue.pending_count("t1") == 2

    def test_submit_different_threads_separate(self):
        """不同 thread_id 的消息独立存储。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        queue.submit("t1", [FakeMessage(type="human", content="a")])
        queue.submit("t2", [FakeMessage(type="human", content="b")])
        assert queue.pending_count("t1") == 1
        assert queue.pending_count("t2") == 1
        assert queue.pending_count() == 2

    @pytest.mark.asyncio
    async def test_flush_calls_handler(self):
        """flush 触发 handler 回调。"""
        handler = AsyncMock()
        queue = DebounceQueue(debounce_seconds=10.0, handler=handler)
        msgs = [FakeMessage(type="human", content="hello")]
        queue.submit("t1", msgs)

        await queue.flush("t1")

        handler.assert_called_once()
        call_args = handler.call_args
        assert call_args[0][0] == "t1"
        assert len(call_args[0][1]) == 1
        assert not queue.has_pending("t1")

    @pytest.mark.asyncio
    async def test_flush_increments_count(self):
        """每次 flush 增加 flush_count。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        queue.submit("t1", [FakeMessage(type="human", content="a")])
        assert queue._flush_count == 0

        await queue.flush("t1")
        assert queue._flush_count == 1

    @pytest.mark.asyncio
    async def test_flush_nonexistent_thread_noop(self):
        """flush 不存在的 thread_id 不报错。"""
        queue = DebounceQueue(debounce_seconds=10.0)
        await queue.flush("nonexistent")
        assert queue._flush_count == 0

    @pytest.mark.asyncio
    async def test_multiple_submits_single_flush(self):
        """多次提交后一次 flush，handler 只调用一次。"""
        handler = AsyncMock()
        queue = DebounceQueue(debounce_seconds=10.0, handler=handler)

        queue.submit("t1", [FakeMessage(type="human", content="a")])
        queue.submit("t1", [FakeMessage(type="human", content="b")])
        queue.submit("t1", [FakeMessage(type="human", content="c")])

        await queue.flush("t1")

        handler.assert_called_once()
        # 合并后的消息应有 3 条
        assert len(handler.call_args[0][1]) == 3

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash(self):
        """handler 异常不会导致队列崩溃。"""
        handler = AsyncMock(side_effect=RuntimeError("处理失败"))
        queue = DebounceQueue(debounce_seconds=10.0, handler=handler)
        queue.submit("t1", [FakeMessage(type="human", content="a")])

        # 不应抛出异常
        await queue.flush("t1")
        assert not queue.has_pending("t1")

    def test_debounce_seconds_property(self):
        """debounce_seconds 属性可读。"""
        queue = DebounceQueue(debounce_seconds=3.0)
        assert queue.debounce_seconds == 3.0


# ══════════════════════════════════════════════════════════
# MemoryStorage 测试
# ══════════════════════════════════════════════════════════


class TestMemoryStorage:
    """MemoryStorage 单元测试。"""

    @pytest.fixture()
    def storage(self, tmp_path: Path) -> MemoryStorage:
        return MemoryStorage(storage_dir=str(tmp_path / "memory"))

    def test_read_nonexistent_returns_empty(self, storage: MemoryStorage):
        """读取不存在的用户记忆返回空字符串。"""
        assert storage.read("unknown_user") == ""

    def test_write_and_read_roundtrip(self, storage: MemoryStorage):
        """写入后读取返回相同内容。"""
        storage.write("user1", "用户偏好：Python")
        result = storage.read("user1")
        assert result == "用户偏好：Python"

    def test_write_creates_directory(self, storage: MemoryStorage):
        """写入时自动创建存储目录。"""
        assert not storage.storage_dir.exists()
        storage.write("user1", "test")
        assert storage.storage_dir.exists()

    def test_write_overwrites_existing(self, storage: MemoryStorage):
        """写入覆盖已有内容。"""
        storage.write("user1", "旧内容")
        storage.write("user1", "新内容")
        assert storage.read("user1") == "新内容"

    def test_write_preserves_other_users(self, storage: MemoryStorage):
        """写入一个用户不影响其他用户。"""
        storage.write("user1", "记忆1")
        storage.write("user2", "记忆2")
        assert storage.read("user1") == "记忆1"
        assert storage.read("user2") == "记忆2"

    def test_exists_false_initially(self, storage: MemoryStorage):
        """初始状态下用户记忆不存在。"""
        assert not storage.exists("user1")

    def test_exists_true_after_write(self, storage: MemoryStorage):
        """写入后 exists 返回 True。"""
        storage.write("user1", "content")
        assert storage.exists("user1")

    def test_delete_removes_file(self, storage: MemoryStorage):
        """删除后文件不存在。"""
        storage.write("user1", "content")
        storage.delete("user1")
        assert not storage.exists("user1")
        assert storage.read("user1") == ""

    def test_delete_nonexistent_no_error(self, storage: MemoryStorage):
        """删除不存在的文件不报错。"""
        storage.delete("nonexistent")

    def test_write_unicode_content(self, storage: MemoryStorage):
        """支持 Unicode 内容。"""
        content = "用户喜欢 🐍 Python 和 日本語"
        storage.write("user1", content)
        assert storage.read("user1") == content

    def test_write_empty_string(self, storage: MemoryStorage):
        """写入空字符串。"""
        storage.write("user1", "")
        assert storage.read("user1") == ""
        assert storage.exists("user1")

    def test_write_multiline_content(self, storage: MemoryStorage):
        """写入多行内容。"""
        content = "第一行\n第二行\n第三行"
        storage.write("user1", content)
        assert storage.read("user1") == content

    def test_atomic_write_no_temp_files_left(self, storage: MemoryStorage):
        """原子写入后不应留下临时文件。"""
        storage.write("user1", "content")
        files = list(storage.storage_dir.iterdir())
        # 只应有 user1.md，没有 .tmp 文件
        assert all(not f.name.endswith(".tmp") for f in files)

    def test_path_injection_sanitized(self, storage: MemoryStorage):
        """路径注入字符被清理。"""
        storage.write("../evil", "hacked")
        # 文件应在 storage_dir 内，而非上级目录
        assert not (storage.storage_dir.parent / "evil.md").exists()
        assert storage.read("../evil") == "hacked"

    def test_write_failure_preserves_old_data(self, storage: MemoryStorage, monkeypatch: pytest.MonkeyPatch):
        """写入失败时保留旧数据（通过 mock os.replace 模拟）。"""
        storage.write("user1", "原始数据")
        assert storage.read("user1") == "原始数据"

        # 模拟 os.replace 失败（原子重命名阶段失败）
        original_replace = os.replace

        def failing_replace(src, dst):
            # 清理临时文件以模拟真实失败场景
            try:
                os.unlink(src)
            except OSError:
                pass
            raise OSError("模拟写入失败")

        monkeypatch.setattr(os, "replace", failing_replace)
        storage.write("user1", "新数据")

        # 恢复后读取，旧数据应保留
        monkeypatch.setattr(os, "replace", original_replace)
        assert storage.read("user1") == "原始数据"


# ══════════════════════════════════════════════════════════
# MemoryChunk 数据模型测试
# ══════════════════════════════════════════════════════════


class TestMemoryChunk:
    """MemoryChunk 数据模型测试。"""

    def test_required_fields(self):
        chunk = MemoryChunk(id="c1", content="测试内容")
        assert chunk.id == "c1"
        assert chunk.content == "测试内容"
        assert chunk.user_id == ""
        assert chunk.thread_id == ""
        assert chunk.embedding == []
        assert chunk.created_at is None
        assert chunk.metadata == {}

    def test_all_fields(self):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        chunk = MemoryChunk(
            id="c2",
            content="完整记忆",
            user_id="u1",
            thread_id="t1",
            embedding=[0.1, 0.2, 0.3],
            created_at=now,
            metadata={"source": "chat"},
        )
        assert chunk.user_id == "u1"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.created_at == now
        assert chunk.metadata["source"] == "chat"


# ══════════════════════════════════════════════════════════
# build_memory_prompt 测试
# ══════════════════════════════════════════════════════════


class TestBuildMemoryPrompt:
    """build_memory_prompt 函数测试。"""

    def test_empty_inputs_returns_empty(self):
        """短期和长期记忆均为空时返回空字符串。"""
        assert build_memory_prompt("", None) == ""
        assert build_memory_prompt("", []) == ""
        assert build_memory_prompt("  ", []) == ""

    def test_short_term_only(self):
        """仅有短期记忆。"""
        result = build_memory_prompt("用户喜欢 Python", None)
        assert "short_term_memory" in result
        assert "用户喜欢 Python" in result
        assert "long_term_memory" not in result

    def test_long_term_only(self):
        """仅有长期记忆。"""
        chunks = [
            MemoryChunk(id="c1", content="之前讨论过机器学习"),
            MemoryChunk(id="c2", content="用户是后端开发者"),
        ]
        result = build_memory_prompt("", chunks)
        assert "long_term_memory" in result
        assert "之前讨论过机器学习" in result
        assert "用户是后端开发者" in result
        assert "short_term_memory" not in result

    def test_both_short_and_long_term(self):
        """同时有短期和长期记忆。"""
        chunks = [MemoryChunk(id="c1", content="历史记忆")]
        result = build_memory_prompt("当前偏好", chunks)
        assert "short_term_memory" in result
        assert "当前偏好" in result
        assert "long_term_memory" in result
        assert "历史记忆" in result

    def test_empty_chunks_ignored(self):
        """空内容的 chunk 被忽略。"""
        chunks = [
            MemoryChunk(id="c1", content=""),
            MemoryChunk(id="c2", content="  "),
            MemoryChunk(id="c3", content="有效内容"),
        ]
        result = build_memory_prompt("", chunks)
        assert "有效内容" in result

    def test_all_empty_chunks_returns_empty(self):
        """所有 chunk 内容为空时返回空字符串。"""
        chunks = [
            MemoryChunk(id="c1", content=""),
            MemoryChunk(id="c2", content="  "),
        ]
        assert build_memory_prompt("", chunks) == ""

    def test_prompt_contains_instruction(self):
        """生成的提示词包含引导语。"""
        result = build_memory_prompt("记忆内容", None)
        assert "记忆上下文" in result

    def test_chunks_separated_by_divider(self):
        """多个 chunk 之间有分隔符。"""
        chunks = [
            MemoryChunk(id="c1", content="记忆A"),
            MemoryChunk(id="c2", content="记忆B"),
        ]
        result = build_memory_prompt("", chunks)
        assert "---" in result


# ══════════════════════════════════════════════════════════
# EmbeddingClient 测试
# ══════════════════════════════════════════════════════════


class TestEmbeddingClient:
    """EmbeddingClient 单元测试。"""

    def _make_fake_embeddings(self):
        """创建一个 fake embeddings 实例。"""
        from unittest.mock import MagicMock

        fake = MagicMock()
        fake.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        fake.embed_query.return_value = [0.7, 0.8, 0.9]
        return fake

    def test_embed_texts_delegates_to_embeddings(self):
        """embed_texts 委托给底层 embeddings 实例。"""
        from hn_agent.memory.embedding import EmbeddingClient

        fake = self._make_fake_embeddings()
        client = EmbeddingClient(embeddings=fake)

        result = client.embed_texts(["hello", "world"])
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        fake.embed_documents.assert_called_once_with(["hello", "world"])

    def test_embed_query_delegates_to_embeddings(self):
        """embed_query 委托给底层 embeddings 实例。"""
        from hn_agent.memory.embedding import EmbeddingClient

        fake = self._make_fake_embeddings()
        client = EmbeddingClient(embeddings=fake)

        result = client.embed_query("test query")
        assert result == [0.7, 0.8, 0.9]
        fake.embed_query.assert_called_once_with("test query")

    def test_embed_texts_empty_list(self):
        """空列表返回空列表。"""
        from hn_agent.memory.embedding import EmbeddingClient

        fake = self._make_fake_embeddings()
        client = EmbeddingClient(embeddings=fake)

        result = client.embed_texts([])
        assert result == []
        fake.embed_documents.assert_not_called()

    def test_model_name_property(self):
        """model_name 属性可读。"""
        from hn_agent.memory.embedding import EmbeddingClient

        fake = self._make_fake_embeddings()
        client = EmbeddingClient(model_name="custom-model", embeddings=fake)
        assert client.model_name == "custom-model"

    def test_embeddings_property(self):
        """embeddings 属性返回底层实例。"""
        from hn_agent.memory.embedding import EmbeddingClient

        fake = self._make_fake_embeddings()
        client = EmbeddingClient(embeddings=fake)
        assert client.embeddings is fake


# ══════════════════════════════════════════════════════════
# VectorStoreProvider Protocol 测试
# ══════════════════════════════════════════════════════════


class TestVectorStoreProvider:
    """VectorStoreProvider Protocol 测试。"""

    def test_chroma_vector_store_is_provider(self):
        """ChromaVectorStore 满足 VectorStoreProvider 协议。"""
        from hn_agent.memory.vector_store import ChromaVectorStore, VectorStoreProvider

        store = ChromaVectorStore(collection_name="test")
        assert isinstance(store, VectorStoreProvider)


# ══════════════════════════════════════════════════════════
# ChromaVectorStore 测试
# ══════════════════════════════════════════════════════════


class TestChromaVectorStore:
    """ChromaVectorStore 单元测试（使用内存模式 ChromaDB）。"""

    def _make_fake_embedding_client(self, dim: int = 3):
        """创建 fake embedding client。"""
        from unittest.mock import MagicMock

        fake = MagicMock()
        counter = [0]

        def embed_texts(texts):
            results = []
            for _ in texts:
                counter[0] += 1
                results.append([float(counter[0])] * dim)
            return results

        def embed_query(query):
            counter[0] += 1
            return [float(counter[0])] * dim

        fake.embed_texts.side_effect = embed_texts
        fake.embed_query.side_effect = embed_query
        return fake

    @pytest.mark.asyncio
    async def test_add_and_search_roundtrip(self):
        """添加记忆后可以通过搜索检索到。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        fake_emb = self._make_fake_embedding_client()
        store = ChromaVectorStore(
            collection_name="test_roundtrip",
            embedding_client=fake_emb,
        )

        memories = [
            MemoryChunk(id="m1", content="用户喜欢 Python 编程"),
            MemoryChunk(id="m2", content="用户是后端开发者"),
        ]
        await store.add_memories(memories)

        results = await store.search("Python", top_k=2)
        assert len(results) > 0
        contents = [r.content for r in results]
        assert any("Python" in c for c in contents)

    @pytest.mark.asyncio
    async def test_add_empty_memories_noop(self):
        """添加空列表不报错。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        store = ChromaVectorStore(collection_name="test_empty")
        await store.add_memories([])

    @pytest.mark.asyncio
    async def test_search_empty_collection(self):
        """空集合搜索返回空列表。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        store = ChromaVectorStore(collection_name="test_search_empty")
        results = await store.search("anything", top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_add_with_precomputed_embeddings(self):
        """使用预计算的嵌入向量添加记忆。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        fake_emb = self._make_fake_embedding_client()
        store = ChromaVectorStore(
            collection_name="test_precomputed",
            embedding_client=fake_emb,
        )

        memories = [
            MemoryChunk(
                id="m1",
                content="预计算向量记忆",
                embedding=[1.0, 1.0, 1.0],
            ),
        ]
        await store.add_memories(memories)

        results = await store.search("预计算", top_k=1)
        assert len(results) == 1
        assert results[0].content == "预计算向量记忆"

    @pytest.mark.asyncio
    async def test_metadata_preserved(self):
        """记忆的元数据在存储和检索后保留。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        fake_emb = self._make_fake_embedding_client()
        store = ChromaVectorStore(
            collection_name="test_metadata",
            embedding_client=fake_emb,
        )

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        memories = [
            MemoryChunk(
                id="m1",
                content="带元数据的记忆",
                user_id="u1",
                thread_id="t1",
                created_at=now,
                metadata={"source": "chat"},
            ),
        ]
        await store.add_memories(memories)

        results = await store.search("元数据", top_k=1)
        assert len(results) == 1
        assert results[0].user_id == "u1"
        assert results[0].thread_id == "t1"
        assert results[0].metadata.get("source") == "chat"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self):
        """相同 ID 的记忆会被更新。"""
        from hn_agent.memory.vector_store import ChromaVectorStore

        fake_emb = self._make_fake_embedding_client()
        store = ChromaVectorStore(
            collection_name="test_upsert",
            embedding_client=fake_emb,
        )

        await store.add_memories([
            MemoryChunk(id="m1", content="旧内容"),
        ])
        await store.add_memories([
            MemoryChunk(id="m1", content="新内容"),
        ])

        results = await store.search("内容", top_k=5)
        contents = [r.content for r in results]
        assert "新内容" in contents
        assert "旧内容" not in contents

    @pytest.mark.asyncio
    async def test_vector_store_error_on_bad_connection(self):
        """连接失败时抛出 VectorStoreError。"""
        from unittest.mock import patch

        from hn_agent.exceptions import VectorStoreError as VSError
        from hn_agent.memory.vector_store import ChromaVectorStore

        store = ChromaVectorStore(
            collection_name="test_error",
            persist_directory="/nonexistent/path/that/should/fail",
        )

        # ChromaDB PersistentClient 可能在某些路径下失败
        # 我们通过 mock 确保异常被正确包装
        with patch("chromadb.PersistentClient", side_effect=Exception("连接失败")):
            with pytest.raises(VSError, match="初始化失败"):
                await store.search("test")


# ══════════════════════════════════════════════════════════
# memory __init__.py 导出测试
# ══════════════════════════════════════════════════════════


class TestMemoryExports:
    """验证 hn_agent.memory 导出所有公开接口。"""

    def test_exports_embedding_client(self):
        from hn_agent.memory import EmbeddingClient
        assert EmbeddingClient is not None

    def test_exports_vector_store_provider(self):
        from hn_agent.memory import VectorStoreProvider
        assert VectorStoreProvider is not None

    def test_exports_chroma_vector_store(self):
        from hn_agent.memory import ChromaVectorStore
        assert ChromaVectorStore is not None

    def test_exports_memory_chunk(self):
        from hn_agent.memory import MemoryChunk
        assert MemoryChunk is not None

    def test_exports_build_memory_prompt(self):
        from hn_agent.memory import build_memory_prompt
        assert build_memory_prompt is not None

    def test_exports_debounce_queue(self):
        from hn_agent.memory import DebounceQueue
        assert DebounceQueue is not None

    def test_exports_memory_storage(self):
        from hn_agent.memory import MemoryStorage
        assert MemoryStorage is not None

    def test_exports_memory_updater(self):
        from hn_agent.memory import MemoryUpdater
        assert MemoryUpdater is not None
