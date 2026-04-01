"""
MCP OAuth 认证处理：为需要授权的 MCP 服务器提供 OAuth 认证流程。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hn_agent.mcp.client import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPOAuthHandler:
    """MCP OAuth 认证处理器。

    管理 OAuth token 的获取和缓存，支持 token 刷新。
    """

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    async def authenticate(self, server_config: MCPServerConfig) -> str:
        """执行 OAuth 认证流程，返回 access token。

        Args:
            server_config: 包含 OAuth 配置的服务器配置。

        Returns:
            access token 字符串。

        Raises:
            MCPConnectionError: 认证失败时抛出。
        """
        from hn_agent.exceptions import MCPConnectionError

        name = server_config.name
        oauth = server_config.oauth

        if oauth is None:
            raise MCPConnectionError(
                f"MCP 服务器 '{name}' 未配置 OAuth"
            )

        # 快速路径：已有 token
        if name in self._tokens:
            logger.debug("使用缓存的 OAuth token: %s", name)
            return self._tokens[name]

        logger.info("正在为 MCP 服务器 '%s' 执行 OAuth 认证", name)

        if not oauth.client_id or not oauth.token_url:
            raise MCPConnectionError(
                f"MCP 服务器 '{name}' 的 OAuth 配置不完整: "
                f"需要 client_id 和 token_url"
            )

        # 占位：实际实现应通过 HTTP 请求获取 token
        # token = await self._request_token(oauth)
        token = f"placeholder_token_{name}"

        self._tokens[name] = token
        logger.info("已获取 MCP 服务器 '%s' 的 OAuth token", name)
        return token

    def get_cached_token(self, server_name: str) -> str | None:
        """获取缓存的 token（如果存在）。"""
        return self._tokens.get(server_name)

    def clear_token(self, server_name: str) -> None:
        """清除指定服务器的缓存 token。"""
        self._tokens.pop(server_name, None)

    def clear_all_tokens(self) -> None:
        """清除所有缓存的 token。"""
        self._tokens.clear()

    @property
    def authenticated_servers(self) -> list[str]:
        """返回已认证的服务器名称列表。"""
        return list(self._tokens.keys())
