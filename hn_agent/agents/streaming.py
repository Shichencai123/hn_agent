"""SSE 流式响应：将 LangGraph 流式输出转换为 SSE 事件流。

事件类型：
  - token: 逐 token 输出
  - tool_call: 工具调用开始
  - tool_result: 工具调用结果
  - subagent_start: 子 Agent 启动
  - subagent_result: 子 Agent 结果
  - done: 推理完成
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, AsyncGenerator

from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)

# 合法的 SSE 事件类型
VALID_EVENT_TYPES = frozenset({
    "token",
    "tool_call",
    "tool_result",
    "subagent_start",
    "subagent_result",
    "done",
})


@dataclass
class SSEEvent:
    """SSE 事件数据模型。

    Attributes:
        event: 事件类型，必须是 VALID_EVENT_TYPES 中的值。
        data: 事件数据字典。
    """

    event: str
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event not in VALID_EVENT_TYPES:
            raise ValueError(
                f"无效的 SSE 事件类型: {self.event!r}，"
                f"合法类型: {sorted(VALID_EVENT_TYPES)}"
            )

    def to_sse_string(self) -> str:
        """序列化为 SSE 协议格式字符串。"""
        data_str = json.dumps(self.data, ensure_ascii=False)
        return f"event: {self.event}\ndata: {data_str}\n\n"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {"event": self.event, "data": self.data}


async def stream_agent_response(
    agent: CompiledStateGraph,
    input_data: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> AsyncGenerator[SSEEvent, None]:
    """将 LangGraph 的流式输出转换为 SSE 事件流。

    遍历 agent.astream_events，根据事件类型映射为 SSEEvent。

    Args:
        agent: 编译后的 LangGraph Agent。
        input_data: Agent 输入数据（通常包含 messages）。
        config: LangGraph 运行配置（如 thread_id 等）。

    Yields:
        SSEEvent 实例。
    """
    config = config or {}

    try:
        async for event in agent.astream_events(input_data, config=config, version="v2"):
            sse_event = _map_langgraph_event(event)
            if sse_event is not None:
                yield sse_event
    except Exception as exc:
        logger.exception("Agent 流式推理异常")
        yield SSEEvent(
            event="done",
            data={"error": str(exc), "finished": True},
        )
        return

    # 推理完成
    yield SSEEvent(event="done", data={"finished": True})


def _map_langgraph_event(event: dict[str, Any]) -> SSEEvent | None:
    """将 LangGraph 流式事件映射为 SSEEvent。

    Args:
        event: LangGraph astream_events 产生的事件字典。

    Returns:
        SSEEvent 或 None（不需要推送的事件）。
    """
    event_kind = event.get("event", "")
    data = event.get("data", {})

    if event_kind == "on_chat_model_stream":
        # token 级别的流式输出
        chunk = data.get("chunk")
        if chunk is not None:
            content = getattr(chunk, "content", "")
            if content:
                return SSEEvent(event="token", data={"content": content})

    elif event_kind == "on_tool_start":
        return SSEEvent(
            event="tool_call",
            data={
                "tool_name": event.get("name", ""),
                "input": data.get("input", {}),
            },
        )

    elif event_kind == "on_tool_end":
        output = data.get("output", "")
        if hasattr(output, "content"):
            output = output.content
        return SSEEvent(
            event="tool_result",
            data={
                "tool_name": event.get("name", ""),
                "output": str(output),
            },
        )

    return None
