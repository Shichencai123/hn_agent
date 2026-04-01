"""路径工具函数：线程 ID 验证、资源路径构建等。"""

from __future__ import annotations

import re
import uuid

# 合法的线程 ID 格式：UUID v4
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_thread_id(thread_id: str) -> bool:
    """检查线程 ID 是否为合法的 UUID v4 格式。"""
    return bool(_UUID_PATTERN.match(thread_id))


def generate_thread_id() -> str:
    """生成新的线程 ID（UUID v4）。"""
    return str(uuid.uuid4())


def build_resource_path(thread_id: str, resource: str) -> str:
    """构建线程下的资源路径。

    Args:
        thread_id: 线程 ID。
        resource: 资源类型（如 "artifacts", "uploads"）。

    Returns:
        资源路径字符串，如 "/api/threads/{id}/artifacts"。
    """
    return f"/api/threads/{thread_id}/{resource}"
