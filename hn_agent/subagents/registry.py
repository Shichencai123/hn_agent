"""
子 Agent 注册表：管理子 Agent 定义的注册和查找。
"""

from __future__ import annotations

import logging
from typing import Iterator

from hn_agent.subagents.config import SubagentDefinition

logger = logging.getLogger(__name__)


class SubagentRegistry:
    """子 Agent 注册表，支持注册和查找子 Agent 定义。"""

    def __init__(self) -> None:
        self._agents: dict[str, SubagentDefinition] = {}

    def register(self, name: str, agent_def: SubagentDefinition) -> None:
        """注册一个子 Agent 定义。

        Args:
            name: 子 Agent 名称（唯一标识）。
            agent_def: 子 Agent 定义。

        Raises:
            ValueError: 如果名称为空。
        """
        if not name:
            raise ValueError("子 Agent 名称不能为空")
        if name in self._agents:
            logger.warning("覆盖已注册的子 Agent: %s", name)
        self._agents[name] = agent_def
        logger.info("已注册子 Agent: %s", name)

    def get(self, name: str) -> SubagentDefinition | None:
        """根据名称查找子 Agent 定义。

        Args:
            name: 子 Agent 名称。

        Returns:
            子 Agent 定义，未找到时返回 None。
        """
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """返回所有已注册的子 Agent 名称列表。"""
        return list(self._agents.keys())

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents

    def __iter__(self) -> Iterator[str]:
        return iter(self._agents)
