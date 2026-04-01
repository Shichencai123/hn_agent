"""
技能系统：Skill 数据模型。

定义技能的核心数据结构，包含名称、描述、依赖工具和提示词内容。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Skill:
    """技能数据模型。

    Attributes:
        name: 技能名称（唯一标识）。
        description: 技能描述。
        dependencies: 依赖的工具名称列表。
        prompt: 技能提示词内容（来自 SKILL.md 的 Markdown body）。
    """

    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    prompt: str = ""
