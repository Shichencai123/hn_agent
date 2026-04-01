"""Artifacts 路由：GET /api/threads/{thread_id}/artifacts。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.gateway.path_utils import is_valid_thread_id

router = APIRouter(prefix="/api", tags=["artifacts"])


class ArtifactInfo(BaseModel):
    """Artifact 信息。"""

    id: str
    type: str
    title: str = ""
    content: str = ""


class ArtifactsResponse(BaseModel):
    """Artifacts 列表响应。"""

    artifacts: list[ArtifactInfo] = Field(default_factory=list)


@router.get("/threads/{thread_id}/artifacts", response_model=ArtifactsResponse)
async def list_artifacts(thread_id: str) -> ArtifactsResponse:
    """获取线程的 Artifacts 列表。"""
    if not is_valid_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="无效的线程 ID 格式")
    return ArtifactsResponse(artifacts=[])
