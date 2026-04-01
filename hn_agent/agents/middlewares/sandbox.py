"""Sandbox 中间件：沙箱生命周期管理。"""

from __future__ import annotations

from typing import Any


class SandboxMiddleware:
    """预处理阶段创建沙箱实例，后处理阶段清理沙箱资源。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 创建沙箱实例
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 清理沙箱资源
        return state
