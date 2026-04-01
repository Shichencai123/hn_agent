"""建议路由：GET /api/threads/{thread_id}/suggestions。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.gateway.path_utils import is_valid_thread_id

router = APIRouter(prefix="/api", tags=["suggestions"])


class SuggestionInfo(BaseModel):
    """建议信息。"""

    id: str
    text: str


class SuggestionsResponse(BaseModel):
    """建议列表响应。"""

    suggestions: list[SuggestionInfo] = Field(default_factory=list)


@router.get("/threads/{thread_id}/suggestions", response_model=SuggestionsResponse)
async def list_suggestions(thread_id: str) -> SuggestionsResponse:
    """获取线程的建议列表。"""
    if not is_valid_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="无效的线程 ID 格式")
    return SuggestionsResponse(suggestions=[])
