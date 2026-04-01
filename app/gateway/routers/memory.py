"""记忆管理路由：GET/PUT /api/memory。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["memory"])


class MemoryEntry(BaseModel):
    """记忆条目。"""

    key: str
    content: str


class MemoryResponse(BaseModel):
    """记忆列表响应。"""

    entries: list[MemoryEntry] = Field(default_factory=list)


class MemoryUpdateRequest(BaseModel):
    """记忆更新请求。"""

    entries: list[MemoryEntry]


class MemoryUpdateResponse(BaseModel):
    """记忆更新响应。"""

    updated: int = 0


@router.get("/memory", response_model=MemoryResponse)
async def get_memory() -> MemoryResponse:
    """获取当前记忆内容。"""
    return MemoryResponse(entries=[])


@router.put("/memory", response_model=MemoryUpdateResponse)
async def update_memory(request: MemoryUpdateRequest) -> MemoryUpdateResponse:
    """更新记忆内容。"""
    return MemoryUpdateResponse(updated=len(request.entries))
