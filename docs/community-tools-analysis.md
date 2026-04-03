# 社区工具深度分析

## 1. 功能概述

社区工具模块集成了四个第三方搜索/抓取服务作为 Agent 的扩展工具：Tavily（AI 搜索引擎）、Jina（网页阅读器/内容提取）、Firecrawl（网页抓取与结构化提取）和 DuckDuckGo（隐私搜索引擎）。每个工具实现为独立的 LangChain `BaseTool`，通过 `ToolLoader` 按名称动态加载。

## 2. 四个社区工具

| 工具 | 功能 | 核心文件 |
|------|------|---------|
| Tavily | AI 驱动的搜索引擎，返回结构化搜索结果 | `hn_agent/community/tavily/tool.py` |
| Jina | 网页内容阅读器，将 URL 转换为干净的文本/Markdown | `hn_agent/community/jina/tool.py` |
| Firecrawl | 网页抓取工具，支持 JavaScript 渲染和结构化提取 | `hn_agent/community/firecrawl/tool.py` |
| DuckDuckGo | 隐私搜索引擎，无需 API Key | `hn_agent/community/duckduckgo/tool.py` |

## 3. 关键代码位置索引

| 文件 | 关键内容 |
|------|---------|
| `hn_agent/community/tavily/tool.py` | TavilySearchTool |
| `hn_agent/community/jina/tool.py` | JinaReaderTool |
| `hn_agent/community/firecrawl/tool.py` | FirecrawlTool |
| `hn_agent/community/duckduckgo/tool.py` | DuckDuckGoSearchTool |
