"""异步 MessageBus：Channel 与 Agent 之间的消息解耦层。"""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

from app.channels.base import ChannelMessage


class MessageBus:
    """基于 asyncio.Queue 的异步消息总线。

    Channel 接收消息后 publish 到总线，
    ChannelManager 通过 subscribe 注册处理器消费消息。
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[ChannelMessage] = asyncio.Queue(maxsize=maxsize)
        self._handlers: list[Callable[[ChannelMessage], Awaitable[None]]] = []
        self._running = False
        self._task: asyncio.Task | None = None

    async def publish(self, message: ChannelMessage) -> None:
        """发布消息到总线。"""
        await self._queue.put(message)

    async def subscribe(self, handler: Callable[[ChannelMessage], Awaitable[None]]) -> None:
        """注册消息处理器。"""
        self._handlers.append(handler)

    async def start(self) -> None:
        """启动消息消费循环。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        """停止消息消费循环。"""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _consume_loop(self) -> None:
        """内部消费循环：从队列取消息并分发给所有处理器。"""
        while self._running:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            for handler in self._handlers:
                try:
                    await handler(message)
                except Exception:
                    # 单个处理器失败不影响其他处理器
                    pass
