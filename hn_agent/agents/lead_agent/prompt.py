"""系统提示词生成：根据 Agent 配置、技能列表和记忆上下文构建系统提示词。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hn_agent.agents.factory import AgentConfig
    from hn_agent.skills.types import Skill

_BASE_PROMPT = (
    "你是一个 AI 超级 Agent，能够使用多种工具完成用户的任务。\n"
    "请根据用户的需求，选择合适的工具并给出准确的回答。"
)


def build_system_prompt(
    agent_config: AgentConfig,
    skills: list[Skill] | None = None,
    memory_context: str = "",
) -> str:
    """根据配置、技能和记忆上下文生成系统提示词。

    拼接顺序：
      1. 基础提示词 + Agent 名称/模型信息
      2. 技能提示词（每个 Skill 的 prompt）
      3. 记忆上下文

    Args:
        agent_config: Agent 配置。
        skills: 已加载的技能列表。
        memory_context: 记忆系统注入的上下文文本。

    Returns:
        完整的系统提示词字符串。
    """
    sections: list[str] = []

    # 1. 基础提示词 + Agent 信息
    agent_info = f"Agent: {agent_config.name} (模型: {agent_config.model_name})"
    sections.append(f"{_BASE_PROMPT}\n\n{agent_info}")

    # 2. 技能提示词
    if skills:
        skill_prompts: list[str] = []
        for skill in skills:
            if skill.prompt and skill.prompt.strip():
                skill_prompts.append(
                    f"### 技能: {skill.name}\n{skill.prompt.strip()}"
                )
        if skill_prompts:
            sections.append(
                "<skills>\n" + "\n\n".join(skill_prompts) + "\n</skills>"
            )

    # 3. 记忆上下文
    if memory_context and memory_context.strip():
        sections.append(memory_context.strip())

    return "\n\n".join(sections)
