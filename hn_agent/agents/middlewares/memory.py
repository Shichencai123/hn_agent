"""Memory 中间件：记忆上下文注入 + 记忆更新队列提交。"""

from __future__ import annotations

from typing import Any


class MemoryMiddleware:
    """预处理阶段注入记忆上下文，后处理阶段提交记忆更新队列。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 从 MemorySystem 检索相关记忆并注入上下文
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 将对话内容提交到记忆更新队列
        return state
