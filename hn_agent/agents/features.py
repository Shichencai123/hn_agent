"""Agent 特性管理：控制 Agent 能力的启用/禁用。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Features:
    """Agent 特性开关。

    通过布尔标志控制 Agent 的各项能力是否启用，
    影响中间件加载和工具集组装。

    Attributes:
        sandbox_enabled: 是否启用沙箱代码执行。
        memory_enabled: 是否启用记忆系统。
        subagent_enabled: 是否启用子 Agent 委派。
        guardrail_enabled: 是否启用护栏授权检查。
        mcp_enabled: 是否启用 MCP 工具集成。
    """

    sandbox_enabled: bool = True
    memory_enabled: bool = True
    subagent_enabled: bool = True
    guardrail_enabled: bool = True
    mcp_enabled: bool = True

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Features:
        """从配置字典创建 Features 实例。

        仅提取已知字段，忽略未知键。

        Args:
            config: 特性配置字典，键为特性名称，值为布尔值。

        Returns:
            Features 实例。
        """
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: bool(v) for k, v in config.items() if k in known_fields}
        return cls(**filtered)
