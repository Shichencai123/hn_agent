"""MCP 服务器列表路由：GET /api/mcp。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["mcp"])


class MCPServerInfo(BaseModel):
    """MCP 服务器信息。"""

    name: str
    transport: str
    status: str = "disconnected"


class MCPResponse(BaseModel):
    """MCP 服务器列表响应。"""

    servers: list[MCPServerInfo] = Field(default_factory=list)


@router.get("/mcp", response_model=MCPResponse)
async def list_mcp_servers() -> MCPResponse:
    """获取已配置的 MCP 服务器列表。"""
    return MCPResponse(servers=[])
