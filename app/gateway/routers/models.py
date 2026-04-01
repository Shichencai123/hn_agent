"""模型列表路由：GET /api/models。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["models"])


class ModelInfo(BaseModel):
    """模型信息。"""

    id: str
    name: str
    provider: str


class ModelsResponse(BaseModel):
    """模型列表响应。"""

    models: list[ModelInfo] = Field(default_factory=list)


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """获取可用模型列表。"""
    return ModelsResponse(
        models=[
            ModelInfo(id="gpt-4o", name="GPT-4o", provider="openai"),
            ModelInfo(id="claude-3-sonnet", name="Claude 3 Sonnet", provider="anthropic"),
        ]
    )
