"""社区工具单元测试：Tavily, Jina, Firecrawl, DuckDuckGo。"""

from __future__ import annotations

import pytest
from langchain_core.tools import BaseTool

from hn_agent.community import (
    DuckDuckGoSearchTool,
    FirecrawlScrapeTool,
    JinaExtractTool,
    TavilySearchTool,
)
from hn_agent.config.models import AppConfig, ModelSettings, ProviderConfig


# ══════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════


def _make_config(**provider_keys: str) -> AppConfig:
    """创建带有指定 provider API 密钥的配置。"""
    providers = {
        name: ProviderConfig(api_key=key) for name, key in provider_keys.items()
    }
    return AppConfig(model=ModelSettings(providers=providers))


# ══════════════════════════════════════════════════════════
# BaseTool 接口一致性测试
# ══════════════════════════════════════════════════════════


ALL_TOOL_CLASSES = [
    TavilySearchTool,
    JinaExtractTool,
    FirecrawlScrapeTool,
    DuckDuckGoSearchTool,
]


class TestCommunityToolInterface:
    """验证所有社区工具满足统一的 BaseTool 接口。"""

    @pytest.mark.parametrize("tool_cls", ALL_TOOL_CLASSES)
    def test_is_base_tool(self, tool_cls):
        """每个社区工具都是 BaseTool 的子类。"""
        tool = tool_cls()
        assert isinstance(tool, BaseTool)

    @pytest.mark.parametrize("tool_cls", ALL_TOOL_CLASSES)
    def test_has_name(self, tool_cls):
        """每个社区工具都有非空的 name。"""
        tool = tool_cls()
        assert tool.name
        assert isinstance(tool.name, str)

    @pytest.mark.parametrize("tool_cls", ALL_TOOL_CLASSES)
    def test_has_description(self, tool_cls):
        """每个社区工具都有非空的 description。"""
        tool = tool_cls()
        assert tool.description
        assert isinstance(tool.description, str)

    @pytest.mark.parametrize("tool_cls", ALL_TOOL_CLASSES)
    def test_has_args_schema(self, tool_cls):
        """每个社区工具都有 args_schema。"""
        tool = tool_cls()
        assert tool.args_schema is not None

    @pytest.mark.parametrize("tool_cls", ALL_TOOL_CLASSES)
    def test_unique_names(self, tool_cls):
        """工具名称在所有社区工具中唯一。"""
        names = [cls().name for cls in ALL_TOOL_CLASSES]
        assert len(names) == len(set(names))


# ══════════════════════════════════════════════════════════
# TavilySearchTool 测试
# ══════════════════════════════════════════════════════════


class TestTavilySearchTool:
    """TavilySearchTool 单元测试。"""

    def test_default_name(self):
        tool = TavilySearchTool()
        assert tool.name == "tavily_search"

    def test_from_config_with_key(self):
        config = _make_config(tavily="test-tavily-key")
        tool = TavilySearchTool.from_config(config)
        assert tool.api_key == "test-tavily-key"

    def test_from_config_without_key(self):
        config = _make_config()
        tool = TavilySearchTool.from_config(config)
        assert tool.api_key == ""

    def test_run_without_api_key_returns_error(self):
        tool = TavilySearchTool(api_key="")
        result = tool._run(query="test")
        assert "error_type" in result
        assert "error_message" in result
        assert result["error_type"] == "ConfigurationError"

    def test_run_with_api_key_raises_not_implemented(self):
        tool = TavilySearchTool(api_key="valid-key")
        with pytest.raises(NotImplementedError, match="Tavily"):
            tool._run(query="test")

    @pytest.mark.asyncio
    async def test_arun_without_api_key_returns_error(self):
        tool = TavilySearchTool(api_key="")
        result = await tool._arun(query="test")
        assert "error_type" in result
        assert result["error_type"] == "ConfigurationError"

    def test_args_schema_has_query(self):
        tool = TavilySearchTool()
        fields = tool.args_schema.model_fields
        assert "query" in fields

    def test_args_schema_has_max_results(self):
        tool = TavilySearchTool()
        fields = tool.args_schema.model_fields
        assert "max_results" in fields


# ══════════════════════════════════════════════════════════
# JinaExtractTool 测试
# ══════════════════════════════════════════════════════════


class TestJinaExtractTool:
    """JinaExtractTool 单元测试。"""

    def test_default_name(self):
        tool = JinaExtractTool()
        assert tool.name == "jina_extract"

    def test_from_config_with_key(self):
        config = _make_config(jina="test-jina-key")
        tool = JinaExtractTool.from_config(config)
        assert tool.api_key == "test-jina-key"

    def test_from_config_without_key(self):
        config = _make_config()
        tool = JinaExtractTool.from_config(config)
        assert tool.api_key == ""

    def test_run_without_api_key_returns_error(self):
        tool = JinaExtractTool(api_key="")
        result = tool._run(url="https://example.com")
        assert "error_type" in result
        assert "error_message" in result
        assert result["error_type"] == "ConfigurationError"

    def test_run_with_api_key_raises_not_implemented(self):
        tool = JinaExtractTool(api_key="valid-key")
        with pytest.raises(NotImplementedError, match="Jina"):
            tool._run(url="https://example.com")

    @pytest.mark.asyncio
    async def test_arun_without_api_key_returns_error(self):
        tool = JinaExtractTool(api_key="")
        result = await tool._arun(url="https://example.com")
        assert "error_type" in result

    def test_args_schema_has_url(self):
        tool = JinaExtractTool()
        fields = tool.args_schema.model_fields
        assert "url" in fields


# ══════════════════════════════════════════════════════════
# FirecrawlScrapeTool 测试
# ══════════════════════════════════════════════════════════


class TestFirecrawlScrapeTool:
    """FirecrawlScrapeTool 单元测试。"""

    def test_default_name(self):
        tool = FirecrawlScrapeTool()
        assert tool.name == "firecrawl_scrape"

    def test_from_config_with_key(self):
        config = _make_config(firecrawl="test-firecrawl-key")
        tool = FirecrawlScrapeTool.from_config(config)
        assert tool.api_key == "test-firecrawl-key"

    def test_from_config_without_key(self):
        config = _make_config()
        tool = FirecrawlScrapeTool.from_config(config)
        assert tool.api_key == ""

    def test_run_without_api_key_returns_error(self):
        tool = FirecrawlScrapeTool(api_key="")
        result = tool._run(url="https://example.com")
        assert "error_type" in result
        assert "error_message" in result
        assert result["error_type"] == "ConfigurationError"

    def test_run_with_api_key_raises_not_implemented(self):
        tool = FirecrawlScrapeTool(api_key="valid-key")
        with pytest.raises(NotImplementedError, match="Firecrawl"):
            tool._run(url="https://example.com")

    @pytest.mark.asyncio
    async def test_arun_without_api_key_returns_error(self):
        tool = FirecrawlScrapeTool(api_key="")
        result = await tool._arun(url="https://example.com")
        assert "error_type" in result

    def test_args_schema_has_url(self):
        tool = FirecrawlScrapeTool()
        fields = tool.args_schema.model_fields
        assert "url" in fields

    def test_args_schema_has_formats(self):
        tool = FirecrawlScrapeTool()
        fields = tool.args_schema.model_fields
        assert "formats" in fields


# ══════════════════════════════════════════════════════════
# DuckDuckGoSearchTool 测试
# ══════════════════════════════════════════════════════════


class TestDuckDuckGoSearchTool:
    """DuckDuckGoSearchTool 单元测试。"""

    def test_default_name(self):
        tool = DuckDuckGoSearchTool()
        assert tool.name == "duckduckgo_search"

    def test_from_config(self):
        """DuckDuckGo 不需要 API 密钥。"""
        config = _make_config()
        tool = DuckDuckGoSearchTool.from_config(config)
        assert isinstance(tool, DuckDuckGoSearchTool)

    def test_run_raises_not_implemented(self):
        tool = DuckDuckGoSearchTool()
        with pytest.raises(NotImplementedError, match="DuckDuckGo"):
            tool._run(query="test")

    @pytest.mark.asyncio
    async def test_arun_raises_not_implemented(self):
        tool = DuckDuckGoSearchTool()
        with pytest.raises(NotImplementedError, match="DuckDuckGo"):
            await tool._arun(query="test")

    def test_args_schema_has_query(self):
        tool = DuckDuckGoSearchTool()
        fields = tool.args_schema.model_fields
        assert "query" in fields

    def test_args_schema_has_max_results(self):
        tool = DuckDuckGoSearchTool()
        fields = tool.args_schema.model_fields
        assert "max_results" in fields


# ══════════════════════════════════════════════════════════
# 导出测试
# ══════════════════════════════════════════════════════════


class TestCommunityExports:
    """验证 hn_agent.community 导出所有公开接口。"""

    def test_exports_tavily(self):
        from hn_agent.community import TavilySearchTool
        assert TavilySearchTool is not None

    def test_exports_jina(self):
        from hn_agent.community import JinaExtractTool
        assert JinaExtractTool is not None

    def test_exports_firecrawl(self):
        from hn_agent.community import FirecrawlScrapeTool
        assert FirecrawlScrapeTool is not None

    def test_exports_duckduckgo(self):
        from hn_agent.community import DuckDuckGoSearchTool
        assert DuckDuckGoSearchTool is not None
