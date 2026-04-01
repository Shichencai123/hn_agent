"""Lead Agent 创建：基于 LangGraph create_react_agent 构建 Agent 图。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from hn_agent.agents.thread_state import ThreadState

logger = logging.getLogger(__name__)


def create_lead_agent(
    model: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """基于 LangGraph create_react_agent 构建 Agent 图。

    Args:
        model: LangChain BaseChatModel 实例。
        tools: 已加载的工具列表。
        system_prompt: 系统提示词。
        checkpointer: 检查点 Provider（可选）。

    Returns:
        编译后的 LangGraph CompiledStateGraph 实例。
    """
    logger.info(
        "创建 Lead Agent: %d 个工具, prompt 长度=%d",
        len(tools),
        len(system_prompt),
    )

    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )

    return agent
