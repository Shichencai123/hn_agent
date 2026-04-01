"""异步 SQLite 检查点 Provider。

对 langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver 的薄封装，
增加损坏数据的容错处理（记录错误日志 + 返回空状态）。
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Sequence

import aiosqlite
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

logger = logging.getLogger(__name__)


class AsyncSQLiteCheckpointer(BaseCheckpointSaver):
    """异步 SQLite 检查点 Provider。

    内部委托给 ``AsyncSqliteSaver``，在 aget/aput 层面捕获损坏数据异常，
    确保不会因为单条检查点损坏而导致整个 Agent 不可用。
    """

    def __init__(self, db_path: str = "./data/checkpoints.db") -> None:
        super().__init__()
        self._db_path = db_path
        self._saver: AsyncSqliteSaver | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    async def _ensure_saver(self) -> AsyncSqliteSaver:
        """懒初始化内部 saver（需要在 async 上下文中创建连接）。"""
        if self._saver is None:
            conn = await aiosqlite.connect(self._db_path)
            self._saver = AsyncSqliteSaver(conn)
            await self._saver.setup()
        return self._saver

    # ── BaseCheckpointSaver 必须实现的异步方法 ────────────

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """异步存储检查点。"""
        try:
            saver = await self._ensure_saver()
            return await saver.aput(config, checkpoint, metadata, new_versions)
        except Exception:
            logger.exception("异步检查点写入失败，config=%s", config)
            raise

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """异步存储中间写入。"""
        try:
            saver = await self._ensure_saver()
            await saver.aput_writes(config, writes, task_id, task_path)
        except Exception:
            logger.exception("异步检查点写入 writes 失败，config=%s", config)
            raise

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """异步读取检查点。

        如果数据损坏或反序列化失败，记录错误并返回 None（调用方将创建空白状态）。
        """
        try:
            saver = await self._ensure_saver()
            return await saver.aget_tuple(config)
        except Exception:
            logger.exception(
                "异步检查点数据损坏或加载失败，返回空白状态。config=%s", config
            )
            return None

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """异步列出检查点。"""
        try:
            saver = await self._ensure_saver()
            async for item in saver.alist(
                config, filter=filter, before=before, limit=limit
            ):
                yield item
        except Exception:
            logger.exception("异步检查点列表查询失败，config=%s", config)
            return

    # ── 同步方法的桩实现（BaseCheckpointSaver 要求） ──────

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        raise NotImplementedError("AsyncSQLiteCheckpointer 仅支持异步操作，请使用 aput")

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        raise NotImplementedError(
            "AsyncSQLiteCheckpointer 仅支持异步操作，请使用 aget_tuple"
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ):
        raise NotImplementedError("AsyncSQLiteCheckpointer 仅支持异步操作，请使用 alist")

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        raise NotImplementedError(
            "AsyncSQLiteCheckpointer 仅支持异步操作，请使用 aput_writes"
        )

    # ── 生命周期 ─────────────────────────────────────────

    async def close(self) -> None:
        """关闭数据库连接。"""
        if self._saver is not None:
            try:
                await self._saver.conn.close()
            except Exception:
                logger.exception("关闭异步检查点数据库连接失败")
            self._saver = None
