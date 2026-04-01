"""
虚拟路径翻译器：将虚拟路径安全地映射到沙箱根目录内的实际路径。

防止路径逃逸攻击（../, 绝对路径, 符号链接）。
"""

from __future__ import annotations

import os
from pathlib import Path

from hn_agent.exceptions import PathEscapeError


def translate_path(virtual_path: str, sandbox_root: str) -> str:
    """将虚拟路径翻译为沙箱内实际路径，防止路径逃逸。

    Args:
        virtual_path: 用户提供的虚拟路径。
        sandbox_root: 沙箱根目录的绝对路径。

    Returns:
        沙箱内的实际绝对路径。

    Raises:
        PathEscapeError: 路径逃逸尝试。
    """
    root = Path(sandbox_root).resolve()

    # 拒绝绝对路径
    if os.path.isabs(virtual_path):
        raise PathEscapeError(f"绝对路径不允许: {virtual_path}")

    # 规范化并解析路径（消除 ../ 等）
    resolved = (root / virtual_path).resolve()

    # 检查解析后的路径是否仍在沙箱根目录内
    try:
        resolved.relative_to(root)
    except ValueError:
        raise PathEscapeError(
            f"路径逃逸: {virtual_path} 解析到沙箱外 ({resolved})"
        )

    # 检查符号链接：如果路径存在且是符号链接，验证其目标
    if resolved.exists() and resolved.is_symlink():
        link_target = resolved.resolve()
        try:
            link_target.relative_to(root)
        except ValueError:
            raise PathEscapeError(
                f"符号链接逃逸: {virtual_path} 指向沙箱外 ({link_target})"
            )

    return str(resolved)
