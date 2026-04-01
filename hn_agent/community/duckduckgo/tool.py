"""
DuckDuckGo 搜索工具：LangChain BaseTool 封装。

DuckDuckGo 搜索不需要 API 密钥，但仍从 Config_System 加载可选配置。
API 调用失败时返回结构化错误结果，不抛出异常。
"""

from __future__ import annotations

import logging
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from hn_agent.config.models import AppConfig

logger = logging.getLogger(__name__)


class DuckDuckGoSearchInput(BaseModel):
    """DuckDuckGo 搜索工具的输入参数。"""

    query: str = Field(description="搜索查询关键词")
    max_results: int = Field(default=5, description="最大返回结果数量")


class DuckDuckGoSearchTool(BaseTool):
    """DuckDuckGo 搜索工具：通过 DuckDuckGo 执行网络搜索（无需 API 密钥）。"""

    name: str = "duckduckgo_search"
    description: str = (
        "使用 DuckDuckGo 执行网络搜索，返回与查询相关的搜索结果列表。"
        "无需 API 密钥，适用于免费的网络搜索场景。"
    )
    args_schema: Type[BaseModel] = DuckDuckGoSearchInput

    @classmethod
    def from_config(cls, config: AppConfig) -> DuckDuckGoSearchTool:
        """从配置系统创建工具实例（DuckDuckGo 无需 API 密钥）。"""
        return cls()

    def _run(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """同步执行 DuckDuckGo 搜索。

        Returns:
            成功时返回 {"results": [...]};
            失败时返回 {"error_type": "...", "error_message": "..."}。
        """
        return self._call_api(query=query, max_results=max_results)

    async def _arun(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """异步执行 DuckDuckGo 搜索。"""
        return self._run(query=query, max_results=max_results)

    def _call_api(self, *, query: str, max_results: int) -> dict[str, Any]:
        """实际调用 DuckDuckGo API（桩实现）。"""
        raise NotImplementedError(
            "DuckDuckGo API 调用尚未实现，需要集成 duckduckgo-search SDK"
        )
