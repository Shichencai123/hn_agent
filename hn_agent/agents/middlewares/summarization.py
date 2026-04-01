"""Summarization 中间件：历史消息摘要压缩。"""

from __future__ import annotations

from typing import Any


class SummarizationMiddleware:
    """预处理阶段在对话超过长度阈值时对历史消息进行摘要压缩。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 检查消息数量，超过阈值时调用 LLM 摘要
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
