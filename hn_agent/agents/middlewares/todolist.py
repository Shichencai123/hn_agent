"""TodoList 中间件：任务列表状态维护。"""

from __future__ import annotations

from typing import Any


class TodoListMiddleware:
    """预处理阶段维护 Agent 的任务列表状态。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 加载和维护任务列表
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
