"""
Jina 内容提取工具：LangChain BaseTool 封装。

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


class JinaExtractInput(BaseModel):
    """Jina 内容提取工具的输入参数。"""

    url: str = Field(description="要提取内容的网页 URL")


class JinaExtractTool(BaseTool):
    """Jina 内容提取工具：通过 Jina API 提取网页的主要文本内容。"""

    name: str = "jina_extract"
    description: str = (
        "使用 Jina API 从指定 URL 提取网页的主要文本内容。"
        "适用于需要获取网页正文、去除广告和导航等干扰内容的场景。"
    )
    args_schema: Type[BaseModel] = JinaExtractInput
    api_key: str = ""

    @classmethod
    def from_config(cls, config: AppConfig) -> JinaExtractTool:
        """从配置系统加载 API 密钥并创建工具实例。"""
        provider = config.model.providers.get("jina", None)
        key_value = provider.api_key if provider and provider.api_key else ""
        return cls(api_key=key_value)

    def _run(self, url: str) -> dict[str, Any]:
        """同步执行 Jina 内容提取。

        Returns:
            成功时返回 {"content": "...", "title": "..."};
            失败时返回 {"error_type": "...", "error_message": "..."}。
        """
        if not self.api_key:
            return {
                "error_type": "ConfigurationError",
                "error_message": "Jina API 密钥未配置",
            }
        return self._call_api(url=url)

    async def _arun(self, url: str) -> dict[str, Any]:
        """异步执行 Jina 内容提取。"""
        return self._run(url=url)

    def _call_api(self, *, url: str) -> dict[str, Any]:
        """实际调用 Jina API（桩实现）。"""
        raise NotImplementedError(
            "Jina API 调用尚未实现，需要集成 Jina Reader API"
        )
