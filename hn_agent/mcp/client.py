"""
MCP 客户端：多服务器连接管理，支持 stdio/SSE/HTTP 传输协议。

实际 MCP SDK 集成为占位实现，聚焦于正确的接口结构和连接管理。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from hn_agent.exceptions import MCPConnectionError

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """MCP 支持的传输协议类型。"""

    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


@dataclass
class OAuthConfig:
    """OAuth 认证配置。"""

    client_id: str = ""
    client_secret: str = ""
    token_url: str = ""
    scopes: list[str] = field(default_factory=list)


@dataclass
class MCPServerConfig:
    """MCP 服务器连接配置。"""

    name: str
    transport: str  # stdio | sse | http
    command: str | None = None  # stdio 模式的启动命令
    url: str | None = None  # SSE/HTTP 模式的服务器 URL
    oauth: OAuthConfig | None = None
    retry_interval: float = 5.0  # 重试间隔（秒）
    max_retries: int = 3


@dataclass
class MCPToolInfo:
    """MCP 服务器提供的工具元信息。"""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """多服务器 MCP 客户端。

    管理与多个 MCP 服务器的连接，支持 stdio/SSE/HTTP 三种传输协议。
    """

    def __init__(self) -> None:
        self._connections: dict[str, MCPServerConfig] = {}
        self._connected: set[str] = set()
        self._tool_cache: dict[str, list[MCPToolInfo]] = {}

    @property
    def connected_servers(self) -> list[str]:
        """返回已连接的服务器名称列表。"""
        return list(self._connected)

    async def connect(self, server_config: MCPServerConfig) -> None:
        """连接到 MCP 服务器。

        Args:
            server_config: 服务器连接配置。

        Raises:
            MCPConnectionError: 连接失败时抛出。
            ValueError: 传输协议不支持时抛出。
        """
        transport = server_config.transport.lower()
        if transport not in {t.value for t in TransportType}:
            raise ValueError(
                f"不支持的传输协议: {transport}，"
                f"支持的协议: {', '.join(t.value for t in TransportType)}"
            )

        name = server_config.name
        logger.info("正在连接 MCP 服务器: %s (transport=%s)", name, transport)

        try:
            if transport == TransportType.STDIO:
                await self._connect_stdio(server_config)
            elif transport == TransportType.SSE:
                await self._connect_sse(server_config)
            elif transport == TransportType.HTTP:
                await self._connect_http(server_config)

            self._connections[name] = server_config
            self._connected.add(name)
            logger.info("已连接 MCP 服务器: %s", name)
        except MCPConnectionError:
            raise
        except Exception as exc:
            raise MCPConnectionError(
                f"连接 MCP 服务器 '{name}' 失败: {exc}"
            ) from exc

    async def disconnect(self, server_name: str) -> None:
        """断开与指定 MCP 服务器的连接。"""
        self._connected.discard(server_name)
        self._connections.pop(server_name, None)
        self._tool_cache.pop(server_name, None)
        logger.info("已断开 MCP 服务器: %s", server_name)

    async def list_tools(self, server_name: str) -> list[MCPToolInfo]:
        """获取指定服务器提供的工具列表。

        Args:
            server_name: 服务器名称。

        Returns:
            工具信息列表。

        Raises:
            MCPConnectionError: 服务器未连接时抛出。
        """
        self._ensure_connected(server_name)

        if server_name in self._tool_cache:
            return self._tool_cache[server_name]

        # 占位：实际实现应通过 MCP 协议获取工具列表
        tools: list[MCPToolInfo] = []
        self._tool_cache[server_name] = tools
        logger.info("已缓存 MCP 服务器 '%s' 的 %d 个工具", server_name, len(tools))
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, args: dict[str, Any]
    ) -> Any:
        """调用指定服务器上的工具。

        Args:
            server_name: 服务器名称。
            tool_name: 工具名称。
            args: 工具调用参数。

        Returns:
            工具执行结果。

        Raises:
            MCPConnectionError: 服务器未连接时抛出。
        """
        self._ensure_connected(server_name)
        logger.info("调用 MCP 工具: %s/%s", server_name, tool_name)

        # 占位：实际实现应通过 MCP 协议转发调用
        return {"status": "not_implemented", "tool": tool_name, "args": args}

    def is_connected(self, server_name: str) -> bool:
        """检查指定服务器是否已连接。"""
        return server_name in self._connected

    def _ensure_connected(self, server_name: str) -> None:
        """确保服务器已连接，否则抛出异常。"""
        if server_name not in self._connected:
            raise MCPConnectionError(
                f"MCP 服务器 '{server_name}' 未连接"
            )

    # ── 传输协议连接实现（占位） ──────────────────────────

    async def _connect_stdio(self, config: MCPServerConfig) -> None:
        """通过 stdio 连接 MCP 服务器（占位实现）。"""
        if not config.command:
            raise MCPConnectionError(
                f"stdio 传输需要 command 配置: {config.name}"
            )

    async def _connect_sse(self, config: MCPServerConfig) -> None:
        """通过 SSE 连接 MCP 服务器（占位实现）。"""
        if not config.url:
            raise MCPConnectionError(
                f"SSE 传输需要 url 配置: {config.name}"
            )

    async def _connect_http(self, config: MCPServerConfig) -> None:
        """通过 HTTP 连接 MCP 服务器（占位实现）。"""
        if not config.url:
            raise MCPConnectionError(
                f"HTTP 传输需要 url 配置: {config.name}"
            )
