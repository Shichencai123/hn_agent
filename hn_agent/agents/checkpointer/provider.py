"""同步 SQLite 检查点 Provider。

对 langgraph.checkpoint.sqlite.SqliteSaver 的薄封装，
增加损坏数据的容错处理（记录错误日志 + 返回空状态）。
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Iterator, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from langgraph.checkpoint.sqlite import SqliteSaver

logger = logging.getLogger(__name__)


class SQLiteCheckpointer(BaseCheckpointSaver):
    """同步 SQLite 检查点 Provider。

    内部委托给 ``SqliteSaver``，在 get/put 层面捕获损坏数据异常，
    确保不会因为单条检查点损坏而导致整个 Agent 不可用。
    """

    def __init__(self, db_path: str = "./data/checkpoints.db") -> None:
        self._db_path = db_path
        self._conn = None
        self._saver = None
        try:
            super().__init__()
            import os
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._saver = SqliteSaver(self._conn)
            self._saver.setup()
        except Exception:
            logger.exception("SQLiteCheckpointer 初始化失败: %s", db_path)
            raise

    @property
    def db_path(self) -> str:
        return self._db_path

    # ── BaseCheckpointSaver 必须实现的方法 ────────────────

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """存储检查点。"""
        try:
            return self._saver.put(config, checkpoint, metadata, new_versions)
        except Exception:
            logger.exception("检查点写入失败，config=%s", config)
            raise

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储中间写入。"""
        try:
            self._saver.put_writes(config, writes, task_id, task_path)
        except Exception:
            logger.exception("检查点写入 writes 失败，config=%s", config)
            raise

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """读取检查点。

        如果数据损坏或反序列化失败，记录错误并返回 None（调用方将创建空白状态）。
        """
        try:
            return self._saver.get_tuple(config)
        except Exception:
            logger.exception(
                "检查点数据损坏或加载失败，返回空白状态。config=%s", config
            )
            return None

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """列出检查点。"""
        try:
            yield from self._saver.list(
                config, filter=filter, before=before, limit=limit
            )
        except Exception:
            logger.exception("检查点列表查询失败，config=%s", config)
            return

    # ── 生命周期 ─────────────────────────────────────────

    def close(self) -> None:
        """关闭数据库连接。"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                logger.exception("关闭检查点数据库连接失败")

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
