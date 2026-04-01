"""
Firecrawl 网页抓取工具：LangChain BaseTool 封装。

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


class FirecrawlScrapeInput(BaseModel):
    """Firecrawl 网页抓取工具的输入参数。"""

    url: str = Field(description="要抓取的网页 URL")
    formats: list[str] = Field(
        default=["markdown"],
        description="输出格式列表，支持 markdown、html 等",
    )


class FirecrawlScrapeTool(BaseTool):
    """Firecrawl 网页抓取工具：通过 Firecrawl API 抓取网页并转换为结构化内容。"""

    name: str = "firecrawl_scrape"
    description: str = (
        "使用 Firecrawl API 抓取指定 URL 的网页内容并转换为 Markdown 等格式。"
        "适用于需要将网页内容转换为结构化文本的场景。"
    )
    args_schema: Type[BaseModel] = FirecrawlScrapeInput
    api_key: str = ""

    @classmethod
    def from_config(cls, config: AppConfig) -> FirecrawlScrapeTool:
        """从配置系统加载 API 密钥并创建工具实例。"""
        provider = config.model.providers.get("firecrawl", None)
        key_value = provider.api_key if provider and provider.api_key else ""
        return cls(api_key=key_value)

    def _run(
        self, url: str, formats: list[str] | None = None
    ) -> dict[str, Any]:
        """同步执行 Firecrawl 网页抓取。

        Returns:
            成功时返回 {"content": "...", "metadata": {...}};
            失败时返回 {"error_type": "...", "error_message": "..."}。
        """
        if formats is None:
            formats = ["markdown"]
        if not self.api_key:
            return {
                "error_type": "ConfigurationError",
                "error_message": "Firecrawl API 密钥未配置",
            }
        return self._call_api(url=url, formats=formats)

    async def _arun(
        self, url: str, formats: list[str] | None = None
    ) -> dict[str, Any]:
        """异步执行 Firecrawl 网页抓取。"""
        return self._run(url=url, formats=formats)

    def _call_api(
        self, *, url: str, formats: list[str]
    ) -> dict[str, Any]:
        """实际调用 Firecrawl API（桩实现）。"""
        raise NotImplementedError(
            "Firecrawl API 调用尚未实现，需要集成 firecrawl-py SDK"
        )
