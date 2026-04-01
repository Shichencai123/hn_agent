"""
技能系统：技能安装器（占位实现）。

支持从外部 URL 安装技能包到本地技能目录。
实际下载和解压逻辑为占位实现，聚焦于正确的接口结构。
"""

from __future__ import annotations

import logging

from hn_agent.skills.loader import SkillLoader
from hn_agent.skills.types import Skill

logger = logging.getLogger(__name__)


class SkillInstaller:
    """技能安装器。

    将外部技能包安装到本地技能目录。
    当前为占位实现，实际安装逻辑待后续集成。
    """

    def __init__(self, loader: SkillLoader | None = None) -> None:
        self._loader = loader

    def install(self, package_url: str, target_dir: str) -> Skill:
        """安装外部技能包。

        Args:
            package_url: 技能包 URL。
            target_dir: 安装目标目录。

        Returns:
            安装后的 Skill 对象。

        Raises:
            NotImplementedError: 当前为占位实现。
        """
        logger.info("安装技能包: %s → %s", package_url, target_dir)
        raise NotImplementedError(
            "技能安装功能尚未实现，当前为占位接口"
        )
