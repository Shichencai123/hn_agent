"""
内置工具：invoke_acp_agent — 调用 ACP Agent。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class InvokeACPAgentInput(BaseModel):
    """ACP Agent 调用工具的输入参数。"""

    agent_url: str = Field(description="ACP Agent 的 URL 地址")
    message: str = Field(description="发送给 ACP Agent 的消息")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="附加元数据"
    )


class InvokeACPAgentTool(BaseTool):
    """调用外部 ACP Agent 的工具。"""

    name: str = "invoke_acp_agent"
    description: str = "通过 ACP 协议调用外部 Agent，发送消息并获取响应。"
    args_schema: Type[BaseModel] = InvokeACPAgentInput

    def _run(
        self,
        agent_url: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """桩实现：返回 ACP Agent 调用请求结构。"""
        return {
            "type": "invoke_acp_agent",
            "agent_url": agent_url,
            "message": message,
            "metadata": metadata or {},
        }
