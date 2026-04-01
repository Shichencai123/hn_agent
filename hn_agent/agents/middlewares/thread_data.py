"""ThreadData 中间件：加载线程关联数据。"""

from __future__ import annotations

from typing import Any


class ThreadDataMiddleware:
    """预处理阶段加载线程关联的数据到 Agent 状态中。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 从持久化存储加载线程数据
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
