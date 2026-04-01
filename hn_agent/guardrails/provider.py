"""
护栏系统：Provider 协议与数据模型。

定义 GuardrailProvider 可插拔协议接口、AuthorizationResult 和 GuardrailContext 数据模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class GuardrailContext:
    """护栏检查的上下文信息。"""

    thread_id: str = ""
    user_id: str = ""
    agent_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationResult:
    """授权检查结果。"""

    authorized: bool
    reason: str | None = None


@runtime_checkable
class GuardrailProvider(Protocol):
    """护栏 Provider 协议接口。

    所有护栏实现必须提供 check_authorization 方法，
    在工具调用执行前进行授权检查。
    """

    async def check_authorization(
        self, tool_name: str, args: dict[str, Any], context: GuardrailContext
    ) -> AuthorizationResult: ...
