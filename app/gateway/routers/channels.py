"""渠道管理路由：GET/POST /api/channels。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["channels"])

VALID_CHANNEL_TYPES = {"feishu", "slack", "telegram"}


class ChannelInfo(BaseModel):
    """渠道信息。"""

    id: str
    name: str
    type: str
    status: str = "inactive"


class ChannelsResponse(BaseModel):
    """渠道列表响应。"""

    channels: list[ChannelInfo] = Field(default_factory=list)


class CreateChannelRequest(BaseModel):
    """创建渠道请求。"""

    name: str
    type: str


@router.get("/channels", response_model=ChannelsResponse)
async def list_channels() -> ChannelsResponse:
    """获取渠道列表。"""
    return ChannelsResponse(channels=[])


@router.post("/channels", response_model=ChannelInfo, status_code=201)
async def create_channel(request: CreateChannelRequest) -> ChannelInfo:
    """创建新渠道。"""
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="渠道名称不能为空")

    if request.type not in VALID_CHANNEL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的渠道类型: {request.type}，支持: {sorted(VALID_CHANNEL_TYPES)}",
        )

    import uuid

    return ChannelInfo(
        id=str(uuid.uuid4()),
        name=request.name,
        type=request.type,
    )
