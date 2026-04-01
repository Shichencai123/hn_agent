"""Agent 管理路由：GET/POST /api/agents。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["agents"])


class AgentInfo(BaseModel):
    """Agent 信息。"""

    id: str
    name: str
    model: str = "gpt-4o"
    status: str = "idle"


class AgentsResponse(BaseModel):
    """Agent 列表响应。"""

    agents: list[AgentInfo] = Field(default_factory=list)


class CreateAgentRequest(BaseModel):
    """创建 Agent 请求。"""

    name: str
    model: str = "gpt-4o"


@router.get("/agents", response_model=AgentsResponse)
async def list_agents() -> AgentsResponse:
    """获取 Agent 列表。"""
    return AgentsResponse(agents=[])


@router.post("/agents", response_model=AgentInfo, status_code=201)
async def create_agent(request: CreateAgentRequest) -> AgentInfo:
    """创建新 Agent。"""
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Agent 名称不能为空")

    import uuid

    return AgentInfo(
        id=str(uuid.uuid4()),
        name=request.name,
        model=request.model,
    )
