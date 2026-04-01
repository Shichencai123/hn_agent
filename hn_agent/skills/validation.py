"""
技能系统：技能文件格式验证。

验证 SKILL.md 文件的结构完整性，包括 YAML frontmatter 和必需字段。
"""

from __future__ import annotations

from hn_agent.exceptions import SkillValidationError

# YAML frontmatter 中的必需字段
REQUIRED_FIELDS = ("name", "description")


def validate_frontmatter(frontmatter: dict, source: str = "") -> None:
    """验证 YAML frontmatter 包含所有必需字段。

    Args:
        frontmatter: 解析后的 frontmatter 字典。
        source: 来源文件路径（用于错误信息）。

    Raises:
        SkillValidationError: 缺少必需字段或字段值无效时抛出。
    """
    errors: list[dict] = []

    for field_name in REQUIRED_FIELDS:
        if field_name not in frontmatter:
            errors.append({
                "field": field_name,
                "error": "missing",
                "message": f"缺少必需字段: {field_name}",
                "source": source,
            })
        elif not isinstance(frontmatter[field_name], str) or not frontmatter[field_name].strip():
            errors.append({
                "field": field_name,
                "error": "empty",
                "message": f"字段不能为空: {field_name}",
                "source": source,
            })

    # dependencies 如果存在，必须是列表或 None（None 视为空列表）
    if "dependencies" in frontmatter:
        deps = frontmatter["dependencies"]
        if deps is not None and not isinstance(deps, list):
            errors.append({
                "field": "dependencies",
                "error": "type",
                "message": "dependencies 必须是列表类型",
                "source": source,
            })

    if errors:
        msg = f"技能文件验证失败"
        if source:
            msg += f" ({source})"
        msg += f": {len(errors)} 个错误"
        raise SkillValidationError(msg, errors=errors)


def validate_skill_content(content: str, source: str = "") -> None:
    """验证 SKILL.md 文件内容的基本结构。

    Args:
        content: 文件完整内容。
        source: 来源文件路径。

    Raises:
        SkillValidationError: 文件结构不合法时抛出。
    """
    errors: list[dict] = []

    if not content.strip():
        errors.append({
            "field": "content",
            "error": "empty",
            "message": "文件内容为空",
            "source": source,
        })
        raise SkillValidationError(
            f"技能文件验证失败: 文件内容为空", errors=errors
        )

    if not content.strip().startswith("---"):
        errors.append({
            "field": "frontmatter",
            "error": "missing",
            "message": "缺少 YAML frontmatter（文件必须以 --- 开头）",
            "source": source,
        })
        raise SkillValidationError(
            f"技能文件验证失败: 缺少 YAML frontmatter", errors=errors
        )

    # 检查是否有闭合的 frontmatter
    stripped = content.strip()
    second_marker = stripped.find("---", 3)
    if second_marker == -1:
        errors.append({
            "field": "frontmatter",
            "error": "unclosed",
            "message": "YAML frontmatter 未闭合（缺少第二个 ---）",
            "source": source,
        })
        raise SkillValidationError(
            f"技能文件验证失败: YAML frontmatter 未闭合", errors=errors
        )
