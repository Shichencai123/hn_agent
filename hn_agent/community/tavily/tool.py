"""
Tavily 搜索工具：LangChain BaseTool 封装。

从 Config_System 加载 API 密钥，提供统一 BaseTool 接口。
API 调用失败时返回结构化错误结果，不抛出异常。
"""

from __future__ import annotations

import logging
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from hn_agent.config.models import AppConfig

logger = logging.getLogger(__name__)


class TavilySearchInput(BaseModel):
    """Tavily 搜索工具的输入参数。"""

    query: str = Field(description="搜索查询关键词")
    max_results: int = Field(default=5, description="最大返回结果数量")


class TavilySearchTool(BaseTool):
    """Tavily 搜索工具：通过 Tavily API 执行网络搜索。"""

    name: str = "tavily_search"
    description: str = (
        "使用 Tavily API 执行网络搜索，返回与查询相关的搜索结果列表。"
        "适用于需要获取最新网络信息的场景。"
    )
    args_schema: Type[BaseModel] = TavilySearchInput
    api_key: str = ""

    @classmethod
    def from_config(cls, config: AppConfig) -> TavilySearchTool:
        """从配置系统加载 API 密钥并创建工具实例。"""
        api_key = (
            config.model.providers.get("tavily", None)
        )
        key_value = api_key.api_key if api_key and api_key.api_key else ""
        return cls(api_key=key_value)

    def _run(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """同步执行 Tavily 搜索。

        Returns:
            成功时返回 {"results": [...]};
            失败时返回 {"error_type": "...", "error_message": "..."}。
        """
        if not self.api_key:
            return {
                "error_type": "ConfigurationError",
                "error_message": "Tavily API 密钥未配置",
            }
        return self._call_api(query=query, max_results=max_results)

    async def _arun(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """异步执行 Tavily 搜索。"""
        return self._run(query=query, max_results=max_results)

    def _call_api(self, *, query: str, max_results: int) -> dict[str, Any]:
        """实际调用 Tavily API（桩实现）。"""
        raise NotImplementedError(
            "Tavily API 调用尚未实现，需要集成 tavily-python SDK"
        )
