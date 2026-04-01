"""文件上传路由：POST /api/threads/{thread_id}/uploads。"""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.gateway.path_utils import is_valid_thread_id

router = APIRouter(prefix="/api", tags=["uploads"])


class UploadResponse(BaseModel):
    """上传响应。"""

    file_id: str
    filename: str
    size: int
    mime_type: str


@router.post("/threads/{thread_id}/uploads", response_model=UploadResponse)
async def upload_file(
    thread_id: str,
    file: UploadFile = File(...),
) -> UploadResponse:
    """上传文件到指定线程。"""
    if not is_valid_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="无效的线程 ID 格式")

    content = await file.read()
    return UploadResponse(
        file_id="stub-file-id",
        filename=file.filename or "unknown",
        size=len(content),
        mime_type=file.content_type or "application/octet-stream",
    )
