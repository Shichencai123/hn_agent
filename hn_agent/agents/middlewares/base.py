"""中间件协议定义。

每个中间件实现 pre_process（预处理）和 post_process（后处理）方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Middleware(Protocol):
    """中间件协议。

    - pre_process: Agent 推理前执行
    - post_process: Agent 推理后执行（逆序执行）
    """

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """预处理：Agent 推理前执行。"""
        ...

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """后处理：Agent 推理后执行（逆序执行）。"""
        ...
