"""线程管理路由：GET/POST /api/threads, POST /api/threads/{id}/chat (SSE)。"""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.gateway.path_utils import is_valid_thread_id, generate_thread_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["threads"])

# Agent 实例缓存：按 model_name 缓存，避免每次请求重建
_agent_cache: dict[str, object] = {}


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


async def _get_or_create_agent(model_name: str):
    """获取缓存的 Agent 实例，不存在则创建。"""
    if model_name not in _agent_cache:
        from hn_agent.agents.factory import AgentConfig, make_lead_agent

        agent_config = AgentConfig(model_name=model_name)
        _agent_cache[model_name] = await make_lead_agent(agent_config)
        logger.info("Agent 已创建并缓存: model=%s", model_name)
    return _agent_cache[model_name]


@router.post("/threads/{thread_id}/chat")
async def chat(thread_id: str, request: ChatRequest):
    """向线程发送消息并获取 SSE 流式响应。"""
    if not is_valid_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="无效的线程 ID 格式")

    if not request.message.strip():
        raise HTTPException(status_code=422, detail="消息内容不能为空")

    from langchain_core.messages import HumanMessage
    from sse_starlette.sse import EventSourceResponse

    from hn_agent.agents.streaming import stream_agent_response

    # Agent 创建在 generator 外面，避免 SSE 首 token 延迟
    try:
        agent = await _get_or_create_agent(request.model)
    except Exception as exc:
        logger.exception("Agent 创建失败: model=%s", request.model)
        raise HTTPException(status_code=500, detail=str(exc))

    async def event_generator():
        """流式返回推理结果。"""
        try:
            input_data = {"messages": [HumanMessage(content=request.message)]}
            config = {"configurable": {"thread_id": thread_id}}

            async for sse_event in stream_agent_response(agent, input_data, config):
                yield sse_event.to_dict()
        except Exception as exc:
            logger.exception("Chat 流式推理失败: thread_id=%s", thread_id)
            yield {
                "event": "done",
                "data": json.dumps(
                    {"error": str(exc), "finished": True}, ensure_ascii=False
                ),
            }

    return EventSourceResponse(event_generator())
