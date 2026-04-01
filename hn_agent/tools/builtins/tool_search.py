"""
内置工具：tool_search — 搜索可用工具。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ToolSearchInput(BaseModel):
    """工具搜索的输入参数。"""

    query: str = Field(description="搜索关键词")
    category: str = Field(
        default="", description="工具类别过滤（builtin/mcp/community）"
    )


class ToolSearchTool(BaseTool):
    """搜索可用工具的工具。"""

    name: str = "tool_search"
    description: str = "搜索当前可用的工具列表，支持按关键词和类别过滤。"
    args_schema: Type[BaseModel] = ToolSearchInput

    def _run(self, query: str, category: str = "") -> Any:
        """桩实现：返回工具搜索请求结构。"""
        return {
            "type": "tool_search",
            "query": query,
            "category": category,
        }
