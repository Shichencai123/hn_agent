"""DanglingToolCall 中间件：检测未完成工具调用。"""

from __future__ import annotations

from typing import Any


class DanglingToolCallMiddleware:
    """预处理阶段检测并处理未完成的工具调用，防止状态不一致。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 检测 messages 中未完成的 tool_call
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
