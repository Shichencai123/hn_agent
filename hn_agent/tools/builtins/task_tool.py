"""
内置工具：task — 子 Agent 任务委派。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    """任务委派工具的输入参数。"""

    agent_name: str = Field(description="目标子 Agent 名称")
    instruction: str = Field(description="委派给子 Agent 的任务指令")
    context: dict[str, Any] = Field(
        default_factory=dict, description="传递给子 Agent 的上下文数据"
    )


class TaskTool(BaseTool):
    """将任务委派给子 Agent 执行的工具。"""

    name: str = "task"
    description: str = (
        "将任务委派给指定的子 Agent 异步执行。"
        "适用于需要专门 Agent 处理的复杂子任务。"
    )
    args_schema: Type[BaseModel] = TaskInput

    def _run(
        self,
        agent_name: str,
        instruction: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """桩实现：返回任务委派请求结构。"""
        return {
            "type": "task",
            "agent_name": agent_name,
            "instruction": instruction,
            "context": context or {},
        }
