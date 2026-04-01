"""线程管理路由：GET/POST /api/threads, POST /api/threads/{id}/chat (SSE)。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.gateway.path_utils import is_valid_thread_id, generate_thread_id

router = APIRouter(prefix="/api", tags=["threads"])


class ThreadInfo(BaseModel):
    """线程信息。"""

    id: str
    title: str = ""
    created_at: str = ""


class ThreadsResponse(BaseModel):
    """线程列表响应。"""

    threads: list[ThreadInfo] = Field(default_factory=list)


class CreateThreadRequest(BaseModel):
    """创建线程请求。"""

    title: str = ""


class ChatRequest(BaseModel):
    """聊天请求。"""

    message: str
    model: str = "gpt-4o"


@router.get("/threads", response_model=ThreadsResponse)
async def list_threads() -> ThreadsResponse:
    """获取线程列表。"""
    return ThreadsResponse(threads=[])


@router.post("/threads", response_model=ThreadInfo, status_code=201)
async def create_thread(request: CreateThreadRequest) -> ThreadInfo:
    """创建新线程。"""
    return ThreadInfo(
        id=generate_thread_id(),
        title=request.title or "新对话",
    )


@router.post("/threads/{thread_id}/chat")
async def chat(thread_id: str, request: ChatRequest):
    """向线程发送消息并获取 SSE 流式响应。"""
    if not is_valid_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="无效的线程 ID 格式")

    if not request.message.strip():
        raise HTTPException(status_code=422, detail="消息内容不能为空")

    from sse_starlette.sse import EventSourceResponse

    async def event_generator():
        """Stub SSE 事件生成器。"""
        yield {"event": "token", "data": '{"content": "这是一个占位响应"}'}
        yield {"event": "done", "data": '{"finished": true}'}

    return EventSourceResponse(event_generator())
