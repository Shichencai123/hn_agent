"""Guardrail 中间件：工具调用授权检查。"""

from __future__ import annotations

from typing import Any


class GuardrailMiddleware:
    """预处理阶段对工具调用进行授权检查。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 调用 GuardrailProvider 检查授权
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
