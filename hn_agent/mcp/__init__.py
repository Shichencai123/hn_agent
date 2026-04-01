"""MCP 集成：多服务器客户端、懒加载缓存、OAuth 支持。"""

from hn_agent.mcp.cache import MCPToolCache
from hn_agent.mcp.client import (
    MCPClient,
    MCPServerConfig,
    MCPToolInfo,
    OAuthConfig,
    TransportType,
)
from hn_agent.mcp.oauth import MCPOAuthHandler
from hn_agent.mcp.tools import MCPToolAdapter, convert_mcp_tool, convert_mcp_tools

__all__ = [
    "MCPClient",
    "MCPOAuthHandler",
    "MCPServerConfig",
    "MCPToolAdapter",
    "MCPToolCache",
    "MCPToolInfo",
    "OAuthConfig",
    "TransportType",
    "convert_mcp_tool",
    "convert_mcp_tools",
]
