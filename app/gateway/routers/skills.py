"""技能列表路由：GET /api/skills。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["skills"])


class SkillInfo(BaseModel):
    """技能信息。"""

    name: str
    description: str = ""
    enabled: bool = True


class SkillsResponse(BaseModel):
    """技能列表响应。"""

    skills: list[SkillInfo] = Field(default_factory=list)


@router.get("/skills", response_model=SkillsResponse)
async def list_skills() -> SkillsResponse:
    """获取已加载的技能列表。"""
    return SkillsResponse(skills=[])
