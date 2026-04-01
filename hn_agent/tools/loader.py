"""
工具加载器：根据 Agent 配置动态加载所需的工具集。

支持四类工具：sandbox 工具、built-in 工具、MCP 工具、community 工具。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import BaseTool

from hn_agent.tools.builtins import (
    ClarificationTool,
    InvokeACPAgentTool,
    PresentFileTool,
    SetupAgentTool,
    TaskTool,
    ToolSearchTool,
    ViewImageTool,
)

logger = logging.getLogger(__name__)


@dataclass
class Features:
    """Agent 特性开关，控制哪些工具类别被加载。"""

    sandbox_enabled: bool = True
    memory_enabled: bool = True
    subagent_enabled: bool = True
    guardrail_enabled: bool = True
    mcp_enabled: bool = True
    builtin_enabled: bool = True


@dataclass
class AgentConfig:
    """工具加载器所需的 Agent 配置。"""

    features: Features = field(default_factory=Features)
    mcp_servers: list[str] = field(default_factory=list)
    community_tools: list[str] = field(default_factory=list)
    sandbox: Any = None  # SandboxProvider 实例


class ToolLoader:
    """根据 Agent 配置动态加载所需的工具集。"""

    def load_tools(self, agent_config: AgentConfig) -> list[BaseTool]:
        """根据 Agent 配置动态加载所需的工具集。

        按顺序加载：sandbox → builtin → MCP → community 工具。
        """
        tools: list[BaseTool] = []

        if agent_config.features.sandbox_enabled and agent_config.sandbox is not None:
            tools.extend(self._load_sandbox_tools(agent_config.sandbox))

        if agent_config.features.builtin_enabled:
            tools.extend(self._load_builtin_tools(agent_config.features))

        if agent_config.features.mcp_enabled and agent_config.mcp_servers:
            tools.extend(self._load_mcp_tools(agent_config.mcp_servers))

        if agent_config.community_tools:
            tools.extend(self._load_community_tools(agent_config.community_tools))

        logger.info("已加载 %d 个工具", len(tools))
        return tools

    def _load_sandbox_tools(self, sandbox: Any) -> list[BaseTool]:
        """加载沙箱工具。

        Args:
            sandbox: SandboxProvider 实例。

        Returns:
            沙箱工具列表（桩实现，返回空列表）。
        """
        logger.debug("加载沙箱工具 (sandbox=%s)", type(sandbox).__name__)
        # 沙箱工具由 sandbox 模块提供，此处为集成占位
        return []

    def _load_builtin_tools(self, features: Features) -> list[BaseTool]:
        """根据特性开关加载内置工具。

        Args:
            features: Agent 特性配置。

        Returns:
            内置工具列表。
        """
        tools: list[BaseTool] = [
            ClarificationTool(),
            PresentFileTool(),
            ViewImageTool(),
            ToolSearchTool(),
        ]

        if features.subagent_enabled:
            tools.append(TaskTool())

        tools.append(InvokeACPAgentTool())
        tools.append(SetupAgentTool())

        logger.debug("已加载 %d 个内置工具", len(tools))
        return tools

    def _load_mcp_tools(self, mcp_servers: list[str]) -> list[BaseTool]:
        """从 MCP 服务器加载工具。

        Args:
            mcp_servers: MCP 服务器名称列表。

        Returns:
            MCP 工具列表（桩实现，返回空列表）。
        """
        logger.debug("加载 MCP 工具: %s", mcp_servers)
        # MCP 工具由 mcp 模块提供，此处为集成占位
        return []

    def _load_community_tools(self, tool_names: list[str]) -> list[BaseTool]:
        """加载社区工具。

        Args:
            tool_names: 社区工具名称列表。

        Returns:
            社区工具列表（桩实现，返回空列表）。
        """
        logger.debug("加载社区工具: %s", tool_names)
        # 社区工具由 community 模块提供，此处为集成占位
        return []
