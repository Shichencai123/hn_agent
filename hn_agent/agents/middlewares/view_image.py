"""ViewImage 中间件：图片数据注入。"""

from __future__ import annotations

from typing import Any


class ViewImageMiddleware:
    """后处理阶段处理 Agent 生成的图片，将图片数据注入到线程状态中。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 处理生成的图片数据
        return state
