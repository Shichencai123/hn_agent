"""
MCP 工具缓存：懒加载机制，首次请求时连接服务器并缓存工具列表。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hn_agent.mcp.client import MCPClient, MCPServerConfig, MCPToolInfo

logger = logging.getLogger(__name__)


class MCPToolCache:
    """MCP 工具懒加载缓存。

    首次请求某服务器的工具时自动连接并缓存工具列表，
    后续请求直接返回缓存结果。
    """

    def __init__(self, client: MCPClient) -> None:
        self._client = client
        self._cache: dict[str, list[MCPToolInfo]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._server_configs: dict[str, MCPServerConfig] = {}

    def register_server(self, config: MCPServerConfig) -> None:
        """注册 MCP 服务器配置，供懒加载时使用。"""
        self._server_configs[config.name] = config

    async def get_tools(self, server_name: str) -> list[MCPToolInfo]:
        """获取指定服务器的工具列表（懒加载）。

        首次调用时连接服务器并缓存工具列表，
        后续调用直接返回缓存。

        Args:
            server_name: 服务器名称。

        Returns:
            工具信息列表。

        Raises:
            MCPConnectionError: 服务器未注册或连接失败。
        """
        # 快速路径：缓存命中
        if server_name in self._cache:
            return self._cache[server_name]

        # 确保每个服务器只有一个并发连接
        lock = self._locks.setdefault(server_name, asyncio.Lock())
        async with lock:
            # 双重检查
            if server_name in self._cache:
                return self._cache[server_name]

            # 懒加载：连接 + 获取工具
            await self._load_tools(server_name)
            return self._cache.get(server_name, [])

    async def _load_tools(self, server_name: str) -> None:
        """连接服务器并加载工具列表到缓存。"""
        from hn_agent.exceptions import MCPConnectionError

        if not self._client.is_connected(server_name):
            config = self._server_configs.get(server_name)
            if config is None:
                raise MCPConnectionError(
                    f"MCP 服务器 '{server_name}' 未注册"
                )
            logger.info("懒加载：正在连接 MCP 服务器 '%s'", server_name)
            await self._client.connect(config)

        tools = await self._client.list_tools(server_name)
        self._cache[server_name] = tools
        logger.info(
            "已缓存 MCP 服务器 '%s' 的 %d 个工具", server_name, len(tools)
        )

    def invalidate(self, server_name: str) -> None:
        """清除指定服务器的缓存。"""
        self._cache.pop(server_name, None)

    def invalidate_all(self) -> None:
        """清除所有缓存。"""
        self._cache.clear()

    @property
    def cached_servers(self) -> list[str]:
        """返回已缓存工具的服务器名称列表。"""
        return list(self._cache.keys())

    def is_cached(self, server_name: str) -> bool:
        """检查指定服务器的工具是否已缓存。"""
        return server_name in self._cache
