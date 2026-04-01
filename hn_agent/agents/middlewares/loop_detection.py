"""LoopDetection 中间件：推理循环检测。"""

from __future__ import annotations

from typing import Any


class LoopDetectionMiddleware:
    """预处理阶段检测 Agent 推理是否进入循环，并在检测到循环时终止推理。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 检测重复动作模式
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
