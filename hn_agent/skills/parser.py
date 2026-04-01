"""
技能系统：SKILL.md 文件解析器。

解析 SKILL.md 文件的 YAML frontmatter 元数据和 Markdown body 内容。
"""

from __future__ import annotations

import yaml

from hn_agent.exceptions import SkillValidationError
from hn_agent.skills.types import Skill
from hn_agent.skills.validation import validate_frontmatter, validate_skill_content


class SkillParser:
    """SKILL.md 文件解析器。

    解析格式：
        ---
        name: skill-name
        description: 技能描述
        dependencies:
          - tool_a
          - tool_b
        ---
        Markdown body（作为 prompt 内容）
    """

    def parse(self, content: str, source: str = "") -> Skill:
        """解析 SKILL.md 文件内容。

        Args:
            content: 文件完整内容。
            source: 来源文件路径（用于错误信息）。

        Returns:
            解析后的 Skill 对象。

        Raises:
            SkillValidationError: 文件格式不合法或缺少必需字段时抛出。
        """
        # 1. 验证基本结构
        validate_skill_content(content, source=source)

        # 2. 分离 frontmatter 和 body
        frontmatter_str, body = self._split_frontmatter(content, source=source)

        # 3. 解析 YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as exc:
            raise SkillValidationError(
                f"YAML frontmatter 解析失败: {exc}",
                errors=[{
                    "field": "frontmatter",
                    "error": "yaml_parse",
                    "message": str(exc),
                    "source": source,
                }],
            ) from exc

        if not isinstance(frontmatter, dict):
            raise SkillValidationError(
                "YAML frontmatter 必须是键值对格式",
                errors=[{
                    "field": "frontmatter",
                    "error": "type",
                    "message": "frontmatter 不是字典类型",
                    "source": source,
                }],
            )

        # 4. 验证必需字段
        validate_frontmatter(frontmatter, source=source)

        # 5. 构建 Skill 对象
        return Skill(
            name=frontmatter["name"].strip(),
            description=frontmatter["description"].strip(),
            dependencies=frontmatter.get("dependencies", []) or [],
            prompt=body.strip(),
        )

    def _split_frontmatter(
        self, content: str, source: str = ""
    ) -> tuple[str, str]:
        """分离 YAML frontmatter 和 Markdown body。

        Returns:
            (frontmatter_str, body) 元组。
        """
        stripped = content.strip()
        # 跳过第一个 ---
        after_first = stripped[3:]
        second_marker = after_first.find("---")

        frontmatter_str = after_first[:second_marker]
        body = after_first[second_marker + 3:]

        return frontmatter_str, body
