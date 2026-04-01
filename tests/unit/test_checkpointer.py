"""检查点系统单元测试。"""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest

from langgraph.checkpoint.base import (
    CheckpointTuple,
    empty_checkpoint,
)


# ── 辅助函数 ─────────────────────────────────────────────


def _make_config(thread_id: str | None = None) -> dict:
    """构造一个最小的 RunnableConfig。"""
    return {
        "configurable": {
            "thread_id": thread_id or uuid.uuid4().hex,
            "checkpoint_ns": "",
        }
    }


# ── 同步 SQLiteCheckpointer 测试 ────────────────────────


class TestSQLiteCheckpointer:
    """同步 SQLiteCheckpointer 测试。"""

    def _make_checkpointer(self, db_path: str):
        from hn_agent.agents.checkpointer import SQLiteCheckpointer

        return SQLiteCheckpointer(db_path=db_path)

    def test_put_and_get_roundtrip(self, tmp_path):
        """写入检查点后能正确读取回来。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            checkpoint = empty_checkpoint()
            metadata = {"source": "test", "step": 0, "writes": {}, "parents": {}}

            returned_config = cp.put(config, checkpoint, metadata, {})

            result = cp.get_tuple(returned_config)
            assert result is not None
            assert isinstance(result, CheckpointTuple)
            assert result.checkpoint["id"] == checkpoint["id"]
        finally:
            cp.close()

    def test_get_nonexistent_returns_none(self, tmp_path):
        """读取不存在的检查点返回 None。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            result = cp.get_tuple(config)
            assert result is None
        finally:
            cp.close()

    def test_list_checkpoints(self, tmp_path):
        """列出检查点。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            checkpoint = empty_checkpoint()
            metadata = {"source": "test", "step": 0, "writes": {}, "parents": {}}
            cp.put(config, checkpoint, metadata, {})

            results = list(cp.list(config))
            assert len(results) >= 1
        finally:
            cp.close()

    def test_db_path_property(self, tmp_path):
        """db_path 属性返回正确路径。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            assert cp.db_path == db_path
        finally:
            cp.close()

    def test_multiple_puts_same_thread(self, tmp_path):
        """同一线程多次写入，get 返回最新的检查点。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            cp1 = empty_checkpoint()
            metadata1 = {"source": "test", "step": 0, "writes": {}, "parents": {}}
            returned1 = cp.put(config, cp1, metadata1, {})

            cp2 = empty_checkpoint()
            metadata2 = {"source": "test", "step": 1, "writes": {}, "parents": {}}
            returned2 = cp.put(returned1, cp2, metadata2, {})

            result = cp.get_tuple(config)
            assert result is not None
            assert result.checkpoint["id"] == cp2["id"]
        finally:
            cp.close()


# ── 异步 AsyncSQLiteCheckpointer 测试 ───────────────────


class TestAsyncSQLiteCheckpointer:
    """异步 AsyncSQLiteCheckpointer 测试。"""

    def _make_checkpointer(self, db_path: str):
        from hn_agent.agents.checkpointer import AsyncSQLiteCheckpointer

        return AsyncSQLiteCheckpointer(db_path=db_path)

    @pytest.mark.asyncio
    async def test_aput_and_aget_roundtrip(self, tmp_path):
        """异步写入检查点后能正确读取回来。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            checkpoint = empty_checkpoint()
            metadata = {"source": "test", "step": 0, "writes": {}, "parents": {}}

            returned_config = await cp.aput(config, checkpoint, metadata, {})

            result = await cp.aget_tuple(returned_config)
            assert result is not None
            assert isinstance(result, CheckpointTuple)
            assert result.checkpoint["id"] == checkpoint["id"]
        finally:
            await cp.close()

    @pytest.mark.asyncio
    async def test_aget_nonexistent_returns_none(self, tmp_path):
        """异步读取不存在的检查点返回 None。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            result = await cp.aget_tuple(config)
            assert result is None
        finally:
            await cp.close()

    @pytest.mark.asyncio
    async def test_alist_checkpoints(self, tmp_path):
        """异步列出检查点。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            checkpoint = empty_checkpoint()
            metadata = {"source": "test", "step": 0, "writes": {}, "parents": {}}
            await cp.aput(config, checkpoint, metadata, {})

            results = []
            async for item in cp.alist(config):
                results.append(item)
            assert len(results) >= 1
        finally:
            await cp.close()

    @pytest.mark.asyncio
    async def test_sync_methods_raise_not_implemented(self, tmp_path):
        """同步方法应抛出 NotImplementedError。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            config = _make_config()
            checkpoint = empty_checkpoint()

            with pytest.raises(NotImplementedError):
                cp.put(config, checkpoint, {}, {})

            with pytest.raises(NotImplementedError):
                cp.get_tuple(config)

            with pytest.raises(NotImplementedError):
                list(cp.list(config))

            with pytest.raises(NotImplementedError):
                cp.put_writes(config, [], "task1")
        finally:
            await cp.close()

    @pytest.mark.asyncio
    async def test_db_path_property(self, tmp_path):
        """db_path 属性返回正确路径。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        try:
            assert cp.db_path == db_path
        finally:
            await cp.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, tmp_path):
        """多次 close 不应报错。"""
        db_path = str(tmp_path / "test.db")
        cp = self._make_checkpointer(db_path)
        await cp._ensure_saver()
        await cp.close()
        await cp.close()  # 第二次 close 不应报错


# ── 模块导入测试 ─────────────────────────────────────────


class TestCheckpointerModule:
    """检查点模块导入和导出测试。"""

    def test_module_exports(self):
        """__init__.py 导出正确的类。"""
        from hn_agent.agents.checkpointer import (
            SQLiteCheckpointer,
            AsyncSQLiteCheckpointer,
        )

        assert SQLiteCheckpointer is not None
        assert AsyncSQLiteCheckpointer is not None

    def test_is_base_checkpoint_saver(self, tmp_path):
        """两个 Provider 都是 BaseCheckpointSaver 的子类。"""
        from langgraph.checkpoint.base import BaseCheckpointSaver
        from hn_agent.agents.checkpointer import (
            SQLiteCheckpointer,
            AsyncSQLiteCheckpointer,
        )

        assert issubclass(SQLiteCheckpointer, BaseCheckpointSaver)
        assert issubclass(AsyncSQLiteCheckpointer, BaseCheckpointSaver)
