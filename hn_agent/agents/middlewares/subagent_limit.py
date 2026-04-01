"""SubagentLimit 中间件：子 Agent 并发限制。"""

from __future__ import annotations

from typing import Any


class SubagentLimitMiddleware:
    """预处理阶段限制子 Agent 的并发数量，防止资源耗尽。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 检查当前并发子 Agent 数量
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
