"""
技能系统：技能发现与加载。

从指定目录发现并加载 SKILL.md 格式的技能文件。
"""

from __future__ import annotations

import logging
import os

from hn_agent.exceptions import SkillValidationError
from hn_agent.skills.parser import SkillParser
from hn_agent.skills.types import Skill

logger = logging.getLogger(__name__)


class SkillLoader:
    """技能发现与加载器。

    扫描指定目录中的 SKILL.md 文件，解析并返回 Skill 对象列表。
    """

    def __init__(self, skills_dir: str = "", parser: SkillParser | None = None) -> None:
        self._skills_dir = skills_dir
        self._parser = parser or SkillParser()
        self._cache: dict[str, Skill] = {}

    @property
    def skills_dir(self) -> str:
        return self._skills_dir

    def discover(self, skills_dir: str | None = None) -> list[Skill]:
        """发现指定目录下的所有技能文件。

        扫描目录中每个子目录的 SKILL.md 文件，解析并返回 Skill 列表。

        Args:
            skills_dir: 技能目录路径。为 None 时使用构造时的默认路径。

        Returns:
            发现的 Skill 对象列表。
        """
        target_dir = skills_dir or self._skills_dir
        if not target_dir or not os.path.isdir(target_dir):
            logger.warning("技能目录不存在或未指定: %s", target_dir)
            return []

        skills: list[Skill] = []

        for entry in sorted(os.listdir(target_dir)):
            entry_path = os.path.join(target_dir, entry)

            # 情况 1: 子目录中的 SKILL.md
            if os.path.isdir(entry_path):
                skill_file = os.path.join(entry_path, "SKILL.md")
                if os.path.isfile(skill_file):
                    skill = self._load_file(skill_file)
                    if skill:
                        skills.append(skill)
                        self._cache[skill.name] = skill

            # 情况 2: 直接放在目录下的 SKILL.md
            elif entry.upper() == "SKILL.MD" and os.path.isfile(entry_path):
                skill = self._load_file(entry_path)
                if skill:
                    skills.append(skill)
                    self._cache[skill.name] = skill

        logger.info("发现 %d 个技能文件", len(skills))
        return skills

    def load(self, skill_name: str) -> Skill:
        """按名称加载技能。

        优先从缓存中查找，未命中时从技能目录加载。

        Args:
            skill_name: 技能名称。

        Returns:
            对应的 Skill 对象。

        Raises:
            SkillValidationError: 技能不存在时抛出。
        """
        if skill_name in self._cache:
            return self._cache[skill_name]

        # 尝试从目录加载
        if self._skills_dir:
            skill_dir = os.path.join(self._skills_dir, skill_name)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            if os.path.isfile(skill_file):
                skill = self._load_file(skill_file)
                if skill:
                    self._cache[skill.name] = skill
                    return skill

        raise SkillValidationError(f"技能 '{skill_name}' 不存在")

    def _load_file(self, file_path: str) -> Skill | None:
        """加载并解析单个 SKILL.md 文件。"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return self._parser.parse(content, source=file_path)
        except SkillValidationError:
            logger.warning("技能文件验证失败: %s", file_path, exc_info=True)
            return None
        except OSError:
            logger.warning("无法读取技能文件: %s", file_path, exc_info=True)
            return None
