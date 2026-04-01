"""Title 中间件：自动生成对话标题。"""

from __future__ import annotations

from typing import Any


class TitleMiddleware:
    """后处理阶段为新对话线程自动生成标题。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 调用 LLM 生成对话标题
        return state
