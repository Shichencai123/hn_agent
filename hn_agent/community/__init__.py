"""
社区工具集成：外部搜索和内容获取工具的 LangChain Tool 封装。

集成工具: Tavily（搜索）、Jina（内容提取）、Firecrawl（网页抓取）、DuckDuckGo（搜索）
"""

from hn_agent.community.tavily.tool import TavilySearchTool
from hn_agent.community.jina.tool import JinaExtractTool
from hn_agent.community.firecrawl.tool import FirecrawlScrapeTool
from hn_agent.community.duckduckgo.tool import DuckDuckGoSearchTool

__all__ = [
    "TavilySearchTool",
    "JinaExtractTool",
    "FirecrawlScrapeTool",
    "DuckDuckGoSearchTool",
]
