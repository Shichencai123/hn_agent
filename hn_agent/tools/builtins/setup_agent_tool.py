"""
内置工具：setup_agent — Agent 设置与配置。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class SetupAgentInput(BaseModel):
    """Agent 设置工具的输入参数。"""

    agent_name: str = Field(description="要设置的 Agent 名称")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Agent 配置参数"
    )


class SetupAgentTool(BaseTool):
    """设置和配置 Agent 的工具。"""

    name: str = "setup_agent"
    description: str = "设置和配置 Agent 实例，包括模型选择、工具配置等。"
    args_schema: Type[BaseModel] = SetupAgentInput

    def _run(
        self,
        agent_name: str,
        config: dict[str, Any] | None = None,
    ) -> Any:
        """桩实现：返回 Agent 设置请求结构。"""
        return {
            "type": "setup_agent",
            "agent_name": agent_name,
            "config": config or {},
        }
