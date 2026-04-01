"""
防抖队列：合并短时间内的多次记忆更新请求。

DebounceQueue 接收记忆更新请求，在可配置的时间窗口内将多次请求合并为一次
LLM 调用，减少不必要的 LLM 开销。
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class _PendingUpdate:
    """待处理的记忆更新请求。"""

    thread_id: str
    messages: list[Any]
    timestamp: float = field(default_factory=time.monotonic)


class DebounceQueue:
    """防抖队列，合并短时间内的多次记忆更新请求为一次处理。

    Parameters
    ----------
    debounce_seconds : float
        防抖窗口时长（秒）。在此窗口内的多次提交会被合并。
    handler : Callable[[str, list[Any]], Awaitable[None]] | None
        实际处理合并后消息的异步回调。为 None 时仅记录日志。
    """

    def __init__(
        self,
        debounce_seconds: float = 5.0,
        handler: Callable[[str, list[Any]], Awaitable[None]] | None = None,
    ) -> None:
        self._debounce_seconds = debounce_seconds
        self._handler = handler
        # thread_id -> 待处理更新
        self._pending: dict[str, _PendingUpdate] = {}
        # thread_id -> 防抖定时器任务
        self._timers: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        # 用于测试：记录已触发的处理次数
        self._flush_count: int = 0

    @property
    def debounce_seconds(self) -> float:
        return self._debounce_seconds

    def submit(self, thread_id: str, messages: list[Any]) -> None:
        """提交记忆更新请求。

        短时间内对同一 thread_id 的多次请求会被合并，消息列表会被拼接。
        防抖窗口到期后统一触发一次处理。

        Parameters
        ----------
        thread_id : str
            线程 ID。
        messages : list
            本次对话的消息列表。
        """
        if not messages:
            return

        # 合并消息到 pending
        if thread_id in self._pending:
            self._pending[thread_id].messages.extend(messages)
            self._pending[thread_id].timestamp = time.monotonic()
        else:
            self._pending[thread_id] = _PendingUpdate(
                thread_id=thread_id,
                messages=list(messages),
            )

        # 重置防抖定时器
        self._reset_timer(thread_id)

    def _reset_timer(self, thread_id: str) -> None:
        """重置指定 thread_id 的防抖定时器。"""
        # 取消已有定时器
        if thread_id in self._timers:
            self._timers[thread_id].cancel()

        try:
            loop = asyncio.get_running_loop()
            self._timers[thread_id] = loop.create_task(
                self._delayed_flush(thread_id)
            )
        except RuntimeError:
            # 没有运行中的事件循环（同步上下文），跳过自动 flush
            logger.debug("无事件循环，跳过自动 flush（thread_id=%s）", thread_id)

    async def _delayed_flush(self, thread_id: str) -> None:
        """等待防抖窗口后触发 flush。"""
        await asyncio.sleep(self._debounce_seconds)
        await self.flush(thread_id)

    async def flush(self, thread_id: str) -> None:
        """立即处理指定 thread_id 的待处理更新。

        Parameters
        ----------
        thread_id : str
            要处理的线程 ID。
        """
        async with self._lock:
            pending = self._pending.pop(thread_id, None)
            self._timers.pop(thread_id, None)

        if pending is None:
            return

        self._flush_count += 1
        logger.info(
            "处理记忆更新: thread_id=%s, messages=%d",
            thread_id,
            len(pending.messages),
        )

        if self._handler is not None:
            try:
                await self._handler(thread_id, pending.messages)
            except Exception:
                logger.exception("记忆更新处理失败: thread_id=%s", thread_id)

    def pending_count(self, thread_id: str | None = None) -> int:
        """返回待处理的更新数量。

        Parameters
        ----------
        thread_id : str | None
            指定线程 ID 时返回该线程的待处理消息数；
            为 None 时返回所有线程的待处理总数。
        """
        if thread_id is not None:
            p = self._pending.get(thread_id)
            return len(p.messages) if p else 0
        return sum(len(p.messages) for p in self._pending.values())

    def has_pending(self, thread_id: str) -> bool:
        """检查指定 thread_id 是否有待处理的更新。"""
        return thread_id in self._pending
