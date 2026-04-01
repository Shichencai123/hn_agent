"""Uploads 中间件：注入上传文件内容。"""

from __future__ import annotations

from typing import Any


class UploadsMiddleware:
    """预处理阶段将上传文件的内容注入到消息上下文中。"""

    async def pre_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        # TODO: 从 UploadManager 获取文件内容并注入
        return state

    async def post_process(
        self, state: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        return state
