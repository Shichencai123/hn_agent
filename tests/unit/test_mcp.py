"""MCP 集成单元测试：MCPClient, MCPToolCache, MCPOAuthHandler, 工具转换。"""

from __future__ import annotations

import pytest

from hn_agent.exceptions import MCPConnectionError
from hn_agent.mcp.client import MCPClient, MCPServerConfig, MCPToolInfo, OAuthConfig, TransportType
from hn_agent.mcp.cache import MCPToolCache
from hn_agent.mcp.oauth import MCPOAuthHandler
from hn_agent.mcp.tools import MCPToolAdapter, convert_mcp_tool, convert_mcp_tools


# ══════════════════════════════════════════════════════════
# MCPClient 测试
# ══════════════════════════════════════════════════════════


class TestMCPClient:
    """MCPClient 单元测试。"""

    def _make_config(
        self,
        name: str = "test-server",
        transport: str = "stdio",
        command: str | None = "echo hello",
        url: str | None = None,
    ) -> MCPServerConfig:
        return MCPServerConfig(
            name=name, transport=transport, command=command, url=url
        )

    @pytest.mark.asyncio
    async def test_connect_stdio(self):
        """stdio 传输协议连接成功。"""
        client = MCPClient()
        config = self._make_config(transport="stdio", command="echo hello")
        await client.connect(config)
        assert client.is_connected("test-server")
        assert "test-server" in client.connected_servers

    @pytest.mark.asyncio
    async def test_connect_sse(self):
        """SSE 传输协议连接成功。"""
        client = MCPClient()
        config = self._make_config(
            transport="sse", command=None, url="http://localhost:8080"
        )
        await client.connect(config)
        assert client.is_connected("test-server")

    @pytest.mark.asyncio
    async def test_connect_http(self):
        """HTTP 传输协议连接成功。"""
        client = MCPClient()
        config = self._make_config(
            transport="http", command=None, url="http://localhost:8080"
        )
        await client.connect(config)
        assert client.is_connected("test-server")

    @pytest.mark.asyncio
    async def test_connect_unsupported_transport_raises(self):
        """不支持的传输协议抛出 ValueError。"""
        client = MCPClient()
        config = self._make_config(transport="grpc")
        with pytest.raises(ValueError, match="不支持的传输协议"):
            await client.connect(config)

    @pytest.mark.asyncio
    async def test_connect_stdio_without_command_raises(self):
        """stdio 模式缺少 command 抛出 MCPConnectionError。"""
        client = MCPClient()
        config = self._make_config(transport="stdio", command=None)
        with pytest.raises(MCPConnectionError, match="command"):
            await client.connect(config)

    @pytest.mark.asyncio
    async def test_connect_sse_without_url_raises(self):
        """SSE 模式缺少 url 抛出 MCPConnectionError。"""
        client = MCPClient()
        config = self._make_config(transport="sse", command=None, url=None)
        with pytest.raises(MCPConnectionError, match="url"):
            await client.connect(config)

    @pytest.mark.asyncio
    async def test_connect_http_without_url_raises(self):
        """HTTP 模式缺少 url 抛出 MCPConnectionError。"""
        client = MCPClient()
        config = self._make_config(transport="http", command=None, url=None)
        with pytest.raises(MCPConnectionError, match="url"):
            await client.connect(config)

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """断开连接后服务器不再可用。"""
        client = MCPClient()
        config = self._make_config()
        await client.connect(config)
        assert client.is_connected("test-server")

        await client.disconnect("test-server")
        assert not client.is_connected("test-server")
        assert "test-server" not in client.connected_servers

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_no_error(self):
        """断开不存在的服务器不报错。"""
        client = MCPClient()
        await client.disconnect("nonexistent")

    @pytest.mark.asyncio
    async def test_list_tools_not_connected_raises(self):
        """未连接时获取工具列表抛出 MCPConnectionError。"""
        client = MCPClient()
        with pytest.raises(MCPConnectionError, match="未连接"):
            await client.list_tools("unknown")

    @pytest.mark.asyncio
    async def test_list_tools_returns_list(self):
        """已连接时返回工具列表。"""
        client = MCPClient()
        await client.connect(self._make_config())
        tools = await client.list_tools("test-server")
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_call_tool_not_connected_raises(self):
        """未连接时调用工具抛出 MCPConnectionError。"""
        client = MCPClient()
        with pytest.raises(MCPConnectionError, match="未连接"):
            await client.call_tool("unknown", "tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_returns_result(self):
        """已连接时调用工具返回结果。"""
        client = MCPClient()
        await client.connect(self._make_config())
        result = await client.call_tool("test-server", "my_tool", {"key": "val"})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_multiple_servers(self):
        """可同时连接多个服务器。"""
        client = MCPClient()
        await client.connect(self._make_config(name="s1"))
        await client.connect(self._make_config(name="s2"))
        assert client.is_connected("s1")
        assert client.is_connected("s2")
        assert len(client.connected_servers) == 2

    def test_initial_state(self):
        """初始状态无连接。"""
        client = MCPClient()
        assert client.connected_servers == []
        assert not client.is_connected("any")


# ══════════════════════════════════════════════════════════
# MCPToolCache 测试
# ══════════════════════════════════════════════════════════


class TestMCPToolCache:
    """MCPToolCache 单元测试。"""

    def _make_config(self, name: str = "cached-server") -> MCPServerConfig:
        return MCPServerConfig(name=name, transport="stdio", command="echo")

    @pytest.mark.asyncio
    async def test_lazy_load_connects_and_caches(self):
        """首次请求时自动连接并缓存。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        config = self._make_config()
        cache.register_server(config)

        tools = await cache.get_tools("cached-server")
        assert isinstance(tools, list)
        assert cache.is_cached("cached-server")
        assert client.is_connected("cached-server")

    @pytest.mark.asyncio
    async def test_second_call_uses_cache(self):
        """第二次调用直接返回缓存。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        config = self._make_config()
        cache.register_server(config)

        tools1 = await cache.get_tools("cached-server")
        tools2 = await cache.get_tools("cached-server")
        assert tools1 is tools2  # 同一对象引用

    @pytest.mark.asyncio
    async def test_unregistered_server_raises(self):
        """未注册的服务器抛出 MCPConnectionError。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        with pytest.raises(MCPConnectionError, match="未注册"):
            await cache.get_tools("unknown")

    def test_invalidate_clears_cache(self):
        """invalidate 清除指定服务器缓存。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        cache._cache["s1"] = []
        cache._cache["s2"] = []

        cache.invalidate("s1")
        assert not cache.is_cached("s1")
        assert cache.is_cached("s2")

    def test_invalidate_all_clears_all(self):
        """invalidate_all 清除所有缓存。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        cache._cache["s1"] = []
        cache._cache["s2"] = []

        cache.invalidate_all()
        assert cache.cached_servers == []

    def test_cached_servers_property(self):
        """cached_servers 返回已缓存的服务器列表。"""
        client = MCPClient()
        cache = MCPToolCache(client)
        assert cache.cached_servers == []

        cache._cache["s1"] = []
        assert "s1" in cache.cached_servers

    @pytest.mark.asyncio
    async def test_already_connected_server_skips_connect(self):
        """已连接的服务器跳过连接步骤。"""
        client = MCPClient()
        config = self._make_config()
        await client.connect(config)

        cache = MCPToolCache(client)
        cache.register_server(config)

        tools = await cache.get_tools("cached-server")
        assert isinstance(tools, list)
        assert cache.is_cached("cached-server")


# ══════════════════════════════════════════════════════════
# MCPOAuthHandler 测试
# ══════════════════════════════════════════════════════════


class TestMCPOAuthHandler:
    """MCPOAuthHandler 单元测试。"""

    def _make_config_with_oauth(
        self, name: str = "oauth-server"
    ) -> MCPServerConfig:
        return MCPServerConfig(
            name=name,
            transport="http",
            url="http://localhost:8080",
            oauth=OAuthConfig(
                client_id="my-client",
                client_secret="my-secret",
                token_url="http://auth.example.com/token",
                scopes=["read", "write"],
            ),
        )

    @pytest.mark.asyncio
    async def test_authenticate_returns_token(self):
        """认证成功返回 token。"""
        handler = MCPOAuthHandler()
        config = self._make_config_with_oauth()
        token = await handler.authenticate(config)
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_caches_token(self):
        """认证后 token 被缓存。"""
        handler = MCPOAuthHandler()
        config = self._make_config_with_oauth()
        token1 = await handler.authenticate(config)
        token2 = await handler.authenticate(config)
        assert token1 == token2

    @pytest.mark.asyncio
    async def test_authenticate_no_oauth_raises(self):
        """无 OAuth 配置时抛出 MCPConnectionError。"""
        handler = MCPOAuthHandler()
        config = MCPServerConfig(
            name="no-oauth", transport="http", url="http://localhost"
        )
        with pytest.raises(MCPConnectionError, match="未配置 OAuth"):
            await handler.authenticate(config)

    @pytest.mark.asyncio
    async def test_authenticate_incomplete_oauth_raises(self):
        """OAuth 配置不完整时抛出 MCPConnectionError。"""
        handler = MCPOAuthHandler()
        config = MCPServerConfig(
            name="bad-oauth",
            transport="http",
            url="http://localhost",
            oauth=OAuthConfig(client_id="", token_url=""),
        )
        with pytest.raises(MCPConnectionError, match="配置不完整"):
            await handler.authenticate(config)

    def test_get_cached_token(self):
        """获取缓存的 token。"""
        handler = MCPOAuthHandler()
        assert handler.get_cached_token("unknown") is None

        handler._tokens["s1"] = "token123"
        assert handler.get_cached_token("s1") == "token123"

    def test_clear_token(self):
        """清除指定服务器的 token。"""
        handler = MCPOAuthHandler()
        handler._tokens["s1"] = "token123"
        handler.clear_token("s1")
        assert handler.get_cached_token("s1") is None

    def test_clear_all_tokens(self):
        """清除所有 token。"""
        handler = MCPOAuthHandler()
        handler._tokens["s1"] = "t1"
        handler._tokens["s2"] = "t2"
        handler.clear_all_tokens()
        assert handler.authenticated_servers == []

    def test_authenticated_servers(self):
        """authenticated_servers 返回已认证的服务器列表。"""
        handler = MCPOAuthHandler()
        assert handler.authenticated_servers == []
        handler._tokens["s1"] = "t1"
        assert "s1" in handler.authenticated_servers


# ══════════════════════════════════════════════════════════
# MCP 工具转换测试
# ══════════════════════════════════════════════════════════


class TestMCPToolConversion:
    """MCP 工具到 LangChain Tool 的转换测试。"""

    def test_convert_simple_tool(self):
        """转换无参数的简单工具。"""
        info = MCPToolInfo(name="ping", description="Ping the server")
        client = MCPClient()
        tool = convert_mcp_tool(info, "s1", client)

        assert tool.name == "ping"
        assert tool.description == "Ping the server"
        assert isinstance(tool, MCPToolAdapter)

    def test_convert_tool_with_parameters(self):
        """转换带参数的工具。"""
        info = MCPToolInfo(
            name="search",
            description="Search for items",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results"},
                },
                "required": ["query"],
            },
        )
        client = MCPClient()
        tool = convert_mcp_tool(info, "s1", client)

        assert tool.name == "search"
        schema = tool.args_schema
        assert schema is not None
        # 验证 schema 包含定义的字段
        fields = schema.model_fields
        assert "query" in fields
        assert "limit" in fields

    def test_convert_tool_empty_description(self):
        """空描述使用默认值。"""
        info = MCPToolInfo(name="noop", description="")
        client = MCPClient()
        tool = convert_mcp_tool(info, "s1", client)
        assert "MCP tool" in tool.description

    def test_convert_mcp_tools_batch(self):
        """批量转换多个工具。"""
        tools_info = [
            MCPToolInfo(name="tool1", description="Tool 1"),
            MCPToolInfo(name="tool2", description="Tool 2"),
            MCPToolInfo(name="tool3", description="Tool 3"),
        ]
        client = MCPClient()
        tools = convert_mcp_tools(tools_info, "s1", client)
        assert len(tools) == 3
        assert [t.name for t in tools] == ["tool1", "tool2", "tool3"]

    def test_convert_mcp_tools_empty_list(self):
        """空列表返回空列表。"""
        client = MCPClient()
        tools = convert_mcp_tools([], "s1", client)
        assert tools == []

    @pytest.mark.asyncio
    async def test_adapter_arun_calls_client(self):
        """MCPToolAdapter._arun 调用 MCP 客户端。"""
        client = MCPClient()
        config = MCPServerConfig(name="s1", transport="stdio", command="echo")
        await client.connect(config)

        info = MCPToolInfo(name="my_tool", description="Test tool")
        tool = convert_mcp_tool(info, "s1", client)

        result = await tool._arun()
        assert isinstance(result, dict)

    def test_adapter_run_raises(self):
        """MCPToolAdapter._run 抛出 NotImplementedError。"""
        info = MCPToolInfo(name="sync_tool", description="Test")
        client = MCPClient()
        tool = convert_mcp_tool(info, "s1", client)

        with pytest.raises(NotImplementedError, match="异步"):
            tool._run()

    def test_convert_tool_various_param_types(self):
        """支持多种参数类型。"""
        info = MCPToolInfo(
            name="multi_type",
            description="Multi-type params",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "count": {"type": "integer"},
                    "ratio": {"type": "number"},
                    "active": {"type": "boolean"},
                    "tags": {"type": "array"},
                    "meta": {"type": "object"},
                },
                "required": [],
            },
        )
        client = MCPClient()
        tool = convert_mcp_tool(info, "s1", client)
        fields = tool.args_schema.model_fields
        assert len(fields) == 6


# ══════════════════════════════════════════════════════════
# TransportType 枚举测试
# ══════════════════════════════════════════════════════════


class TestTransportType:
    """TransportType 枚举测试。"""

    def test_values(self):
        assert TransportType.STDIO.value == "stdio"
        assert TransportType.SSE.value == "sse"
        assert TransportType.HTTP.value == "http"

    def test_all_types(self):
        assert len(TransportType) == 3


# ══════════════════════════════════════════════════════════
# MCP __init__.py 导出测试
# ══════════════════════════════════════════════════════════


class TestMCPExports:
    """验证 hn_agent.mcp 导出所有公开接口。"""

    def test_exports_mcp_client(self):
        from hn_agent.mcp import MCPClient
        assert MCPClient is not None

    def test_exports_mcp_tool_cache(self):
        from hn_agent.mcp import MCPToolCache
        assert MCPToolCache is not None

    def test_exports_mcp_oauth_handler(self):
        from hn_agent.mcp import MCPOAuthHandler
        assert MCPOAuthHandler is not None

    def test_exports_mcp_server_config(self):
        from hn_agent.mcp import MCPServerConfig
        assert MCPServerConfig is not None

    def test_exports_mcp_tool_info(self):
        from hn_agent.mcp import MCPToolInfo
        assert MCPToolInfo is not None

    def test_exports_oauth_config(self):
        from hn_agent.mcp import OAuthConfig
        assert OAuthConfig is not None

    def test_exports_transport_type(self):
        from hn_agent.mcp import TransportType
        assert TransportType is not None

    def test_exports_convert_mcp_tool(self):
        from hn_agent.mcp import convert_mcp_tool
        assert convert_mcp_tool is not None

    def test_exports_convert_mcp_tools(self):
        from hn_agent.mcp import convert_mcp_tools
        assert convert_mcp_tools is not None

    def test_exports_mcp_tool_adapter(self):
        from hn_agent.mcp import MCPToolAdapter
        assert MCPToolAdapter is not None
