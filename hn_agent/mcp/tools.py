"""
MCP 工具适配器：将 MCP 工具转换为 LangChain BaseTool 格式。
"""

from __future__ import annotations

import logging
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, create_model

from hn_agent.mcp.client import MCPClient, MCPToolInfo

logger = logging.getLogger(__name__)


def _build_args_schema(tool_info: MCPToolInfo) -> Type[BaseModel]:
    """根据 MCP 工具参数定义动态构建 Pydantic 模型。"""
    params = tool_info.parameters
    if not params:
        return create_model(f"{tool_info.name}Args")

    properties = params.get("properties", {})
    required = set(params.get("required", []))

    field_definitions: dict[str, Any] = {}
    for name, schema in properties.items():
        field_type = _json_type_to_python(schema.get("type", "string"))
        description = schema.get("description", "")
        if name in required:
            field_definitions[name] = (
                field_type,
                Field(description=description),
            )
        else:
            field_definitions[name] = (
                field_type,
                Field(default=None, description=description),
            )

    return create_model(f"{tool_info.name}Args", **field_definitions)


def _json_type_to_python(json_type: str) -> type:
    """将 JSON Schema 类型映射为 Python 类型。"""
    mapping: dict[str, type] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    return mapping.get(json_type, str)


class MCPToolAdapter(BaseTool):
    """将单个 MCP 工具适配为 LangChain BaseTool。"""

    server_name: str = ""
    mcp_client: Any = None  # MCPClient 实例

    def _run(self, **kwargs: Any) -> Any:
        """同步调用（不支持，MCP 工具仅支持异步）。"""
        raise NotImplementedError("MCP 工具仅支持异步调用，请使用 _arun")

    async def _arun(self, **kwargs: Any) -> Any:
        """异步调用 MCP 工具。"""
        if self.mcp_client is None:
            return {"error": "MCP client not configured"}
        return await self.mcp_client.call_tool(
            self.server_name, self.name, kwargs
        )


def convert_mcp_tool(
    tool_info: MCPToolInfo,
    server_name: str,
    client: MCPClient,
) -> BaseTool:
    """将单个 MCP 工具信息转换为 LangChain BaseTool。

    Args:
        tool_info: MCP 工具元信息。
        server_name: 所属服务器名称。
        client: MCP 客户端实例。

    Returns:
        LangChain BaseTool 实例。
    """
    args_schema = _build_args_schema(tool_info)

    tool = MCPToolAdapter(
        name=tool_info.name,
        description=tool_info.description or f"MCP tool: {tool_info.name}",
        args_schema=args_schema,
        server_name=server_name,
        mcp_client=client,
    )
    return tool


def convert_mcp_tools(
    tools: list[MCPToolInfo],
    server_name: str,
    client: MCPClient,
) -> list[BaseTool]:
    """批量将 MCP 工具转换为 LangChain BaseTool 列表。

    Args:
        tools: MCP 工具元信息列表。
        server_name: 所属服务器名称。
        client: MCP 客户端实例。

    Returns:
        LangChain BaseTool 实例列表。
    """
    result: list[BaseTool] = []
    for info in tools:
        try:
            tool = convert_mcp_tool(info, server_name, client)
            result.append(tool)
        except Exception:
            logger.warning(
                "转换 MCP 工具 '%s/%s' 失败，已跳过",
                server_name,
                info.name,
                exc_info=True,
            )
    return result
