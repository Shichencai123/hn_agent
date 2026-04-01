"""嵌入式客户端：无需 HTTP 的进程内 Agent 访问接口。

提供与 Gateway API 对齐的方法接口，复用 Config_System 加载配置。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from hn_agent.agents.streaming import SSEEvent

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """chat 方法的同步响应。"""

    thread_id: str
    content: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)


@dataclass
class ThreadInfo:
    """线程信息。"""

    thread_id: str
    title: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0


class HarnessClient:
    """嵌入式客户端：进程内直接调用 Lead Agent。

    提供与 Gateway API 对齐的方法接口：
      - chat: 同步返回完整响应
      - stream: 异步生成器流式响应
      - get_thread: 获取线程信息
      - list_threads: 列出所有线程

    Usage::

        client = HarnessClient()
        response = await client.chat("thread-1", "你好")
    """

    def __init__(
        self,
        config_path: str | None = None,
        *,
        agent_config: dict[str, Any] | None = None,
    ) -> None:
        """初始化嵌入式客户端。

        Args:
            config_path: 配置文件路径（可选）。
            agent_config: Agent 配置字典覆盖（可选）。
        """
        self._config_path = config_path
        self._agent_config_override = agent_config or {}
        self._threads: dict[str, ThreadInfo] = {}
        self._agent = None

    async def _ensure_agent(self):
        """确保 Agent 实例已创建（懒加载）。"""
        if self._agent is not None:
            return

        from hn_agent.agents.factory import AgentConfig, make_lead_agent
        from hn_agent.agents.features import Features

        # 构建 AgentConfig
        features_dict = self._agent_config_override.get("features", {})
        features = Features.from_config(features_dict) if features_dict else Features()

        config = AgentConfig(
            agent_id=self._agent_config_override.get("agent_id", "embedded"),
            name=self._agent_config_override.get("name", "Embedded Agent"),
            model_name=self._agent_config_override.get("model_name", "gpt-4o"),
            features=features,
            skill_names=self._agent_config_override.get("skill_names", []),
            mcp_servers=self._agent_config_override.get("mcp_servers", []),
            community_tools=self._agent_config_override.get("community_tools", []),
        )

        self._agent = await make_lead_agent(config)

    def _ensure_thread(self, thread_id: str) -> ThreadInfo:
        """确保线程存在，不存在则创建。"""
        if thread_id not in self._threads:
            self._threads[thread_id] = ThreadInfo(thread_id=thread_id)
        return self._threads[thread_id]

    async def chat(
        self,
        thread_id: str,
        message: str,
        **kwargs: Any,
    ) -> ChatResponse:
        """同步返回完整响应。

        创建 Lead Agent 实例，收集所有流式 token 后返回完整响应。

        Args:
            thread_id: 线程 ID。
            message: 用户消息。
            **kwargs: 传递给 Agent 的额外参数。

        Returns:
            ChatResponse 包含完整响应内容。
        """
        await self._ensure_agent()
        thread_info = self._ensure_thread(thread_id)
        thread_info.message_count += 1

        # 收集所有 token
        content_parts: list[str] = []
        async for event in self.stream(thread_id, message, **kwargs):
            if event.event == "token":
                content_parts.append(event.data.get("content", ""))

        content = "".join(content_parts)
        thread_info.message_count += 1  # Agent 回复也算一条

        return ChatResponse(
            thread_id=thread_id,
            content=content,
        )

    async def stream(
        self,
        thread_id: str,
        message: str,
        **kwargs: Any,
    ) -> AsyncGenerator[SSEEvent, None]:
        """异步生成器流式响应。

        Args:
            thread_id: 线程 ID。
            message: 用户消息。
            **kwargs: 传递给 Agent 的额外参数。

        Yields:
            SSEEvent 实例。
        """
        from langchain_core.messages import HumanMessage
        from hn_agent.agents.streaming import stream_agent_response

        await self._ensure_agent()
        self._ensure_thread(thread_id)

        input_data = {"messages": [HumanMessage(content=message)]}
        config = {"configurable": {"thread_id": thread_id}, **kwargs}

        async for event in stream_agent_response(self._agent, input_data, config):
            yield event

    async def get_thread(self, thread_id: str) -> ThreadInfo:
        """获取线程信息。

        Args:
            thread_id: 线程 ID。

        Returns:
            ThreadInfo 实例。

        Raises:
            KeyError: 线程不存在。
        """
        if thread_id not in self._threads:
            raise KeyError(f"线程不存在: {thread_id}")
        return self._threads[thread_id]

    async def list_threads(self) -> list[ThreadInfo]:
        """列出所有线程。

        Returns:
            ThreadInfo 列表，按创建时间排序。
        """
        return sorted(
            self._threads.values(),
            key=lambda t: t.created_at,
        )
