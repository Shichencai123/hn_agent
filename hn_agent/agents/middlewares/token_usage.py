"""TokenUsage 中间件：Token 用量统计。"""

from __future__ import annotations

from typing import Any


class TokenUsageMiddleware:
    """后处理阶段统计并记录本次推理的 Token 使用量。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 统计 Token 用量
        return state
