"""Agent 工厂：根据配置创建完整的 Lead Agent 实例。

组装流程：
  1. 解析特性配置 (Features)
  2. 选择模型 (Model Factory)
  3. 加载工具 (Tool Loader)
  4. 组装中间件链 (Middleware Chain)
  5. 生成系统提示词 (Prompt Builder)
  6. 创建 LangGraph Agent
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from hn_agent.agents.features import Features

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent 创建所需的完整配置。

    Attributes:
        agent_id: Agent 唯一标识。
        name: Agent 显示名称。
        model_name: LLM 模型名称（如 "gpt-4o"）。
        features: 特性开关配置。
        skill_names: 需要加载的技能名称列表。
        mcp_servers: MCP 服务器名称列表。
        community_tools: 社区工具名称列表。
        custom_settings: 自定义扩展配置。
    """

    agent_id: str = "default"
    name: str = "Lead Agent"
    model_name: str = "gpt-4o"
    features: Features = field(default_factory=Features)
    skill_names: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    community_tools: list[str] = field(default_factory=list)
    custom_settings: dict[str, Any] = field(default_factory=dict)


async def make_lead_agent(agent_config: AgentConfig) -> CompiledStateGraph:
    """根据配置创建完整的 Lead Agent 实例。

    组装流程：
      1. 选择模型 (Model Factory)
      2. 加载工具 (Tool Loader)
      3. 加载技能并生成系统提示词
      4. 创建检查点 Provider
      5. 创建 LangGraph Agent

    Args:
        agent_config: Agent 完整配置。

    Returns:
        编译后的 CompiledStateGraph 实例。

    Raises:
        UnsupportedProviderError: 模型名称不受支持。
        CredentialError: API 凭证缺失。
    """
    from hn_agent.agents.lead_agent.agent import create_lead_agent
    from hn_agent.agents.lead_agent.prompt import build_system_prompt
    from hn_agent.config.loader import ConfigLoader
    from hn_agent.models.factory import create_model
    from hn_agent.tools.loader import ToolLoader
    from hn_agent.tools.loader import AgentConfig as ToolAgentConfig
    from hn_agent.tools.loader import Features as ToolFeatures

    logger.info("开始创建 Lead Agent: %s (model=%s)", agent_config.name, agent_config.model_name)

    # 1. 加载应用配置
    loader = ConfigLoader()
    try:
        app_config = loader.load_from_dict({})
    except Exception:
        logger.warning("无法加载应用配置，使用默认配置")
        from hn_agent.config.models import AppConfig
        app_config = AppConfig()

    # 2. 创建模型
    model = create_model(
        agent_config.model_name,
        config=app_config.model,
    )

    # 3. 加载工具
    tool_features = ToolFeatures(
        sandbox_enabled=agent_config.features.sandbox_enabled,
        memory_enabled=agent_config.features.memory_enabled,
        subagent_enabled=agent_config.features.subagent_enabled,
        guardrail_enabled=agent_config.features.guardrail_enabled,
        mcp_enabled=agent_config.features.mcp_enabled,
    )
    tool_config = ToolAgentConfig(
        features=tool_features,
        mcp_servers=agent_config.mcp_servers,
        community_tools=agent_config.community_tools,
    )
    tool_loader = ToolLoader()
    tools = tool_loader.load_tools(tool_config)

    # 4. 加载技能并生成系统提示词
    skills = _load_skills(agent_config.skill_names)
    system_prompt = build_system_prompt(
        agent_config=agent_config,
        skills=skills,
        memory_context="",
    )

    # 5. 创建检查点 Provider
    checkpointer = _create_checkpointer()

    # 6. 创建 Agent
    agent = create_lead_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )

    logger.info("Lead Agent 创建完成: %s", agent_config.name)
    return agent


def _load_skills(skill_names: list[str]) -> list:
    """加载指定名称的技能列表。

    Args:
        skill_names: 技能名称列表。

    Returns:
        Skill 对象列表。
    """
    if not skill_names:
        return []

    try:
        from hn_agent.skills.loader import SkillLoader
        loader = SkillLoader()
        skills = []
        for name in skill_names:
            try:
                skill = loader.load(name)
                skills.append(skill)
            except Exception:
                logger.warning("技能加载失败: %s", name)
        return skills
    except Exception:
        logger.warning("技能系统不可用")
        return []


def _create_checkpointer():
    """创建检查点 Provider。

    Returns:
        SQLiteCheckpointer 实例，失败时返回 None。
    """
    try:
        from hn_agent.agents.checkpointer import SQLiteCheckpointer
        return SQLiteCheckpointer()
    except Exception:
        logger.warning("检查点系统不可用，Agent 状态不会持久化")
        return None
