"""Clarification 中间件：澄清需求检测。"""

from __future__ import annotations

from typing import Any


class ClarificationMiddleware:
    """预处理阶段检测 Agent 是否需要向用户请求澄清信息。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 检测是否需要澄清
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
