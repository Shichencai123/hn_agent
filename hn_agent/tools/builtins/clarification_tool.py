"""
内置工具：clarification — 向用户请求澄清信息。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ClarificationInput(BaseModel):
    """澄清工具的输入参数。"""

    question: str = Field(description="需要向用户澄清的问题")
    options: list[str] = Field(
        default_factory=list, description="可选的回答选项列表"
    )


class ClarificationTool(BaseTool):
    """向用户请求澄清信息的工具。

    当 Agent 无法确定用户意图时，使用此工具向用户提出澄清问题。
    """

    name: str = "clarification"
    description: str = (
        "向用户请求澄清信息。当无法确定用户意图或需要更多上下文时使用。"
    )
    args_schema: Type[BaseModel] = ClarificationInput

    def _run(self, question: str, options: list[str] | None = None) -> Any:
        """桩实现：返回澄清请求结构。"""
        return {
            "type": "clarification",
            "question": question,
            "options": options or [],
        }
