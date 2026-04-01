"""中间件链：按固定顺序执行 pre_process（正序）和 post_process（逆序）。"""

from __future__ import annotations

from typing import Any

from hn_agent.agents.middlewares.base import Middleware


class MiddlewareChain:
    """中间件链管理器。

    - run_pre: 按正序执行所有中间件的 pre_process
    - run_post: 按逆序执行所有中间件的 post_process
    """

    def __init__(self, middlewares: list[Middleware] | None = None) -> None:
        self.middlewares: list[Middleware] = list(middlewares or [])

    async def run_pre(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """按正序执行所有中间件的预处理。"""
        for mw in self.middlewares:
            state = await mw.pre_process(state, config)
        return state

    async def run_post(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """按逆序执行所有中间件的后处理。"""
        for mw in reversed(self.middlewares):
            state = await mw.post_process(state, config)
        return state
