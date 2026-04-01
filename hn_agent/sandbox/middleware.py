"""
沙箱中间件：管理沙箱实例的生命周期（创建/清理）。

在 Agent 预处理阶段创建沙箱，后处理阶段清理资源。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from hn_agent.sandbox.local.provider import LocalProvider


class SandboxMiddleware:
    """沙箱生命周期管理中间件。"""

    def __init__(self, work_dir: str = "./data/sandbox", timeout: int = 30) -> None:
        self.work_dir = work_dir
        self.timeout = timeout
        self._sandbox_dir: str | None = None
        self._provider: LocalProvider | None = None

    @property
    def provider(self) -> LocalProvider | None:
        """当前活跃的沙箱 Provider。"""
        return self._provider

    async def pre_process(self) -> LocalProvider:
        """预处理：创建沙箱实例。"""
        base = Path(self.work_dir)
        base.mkdir(parents=True, exist_ok=True)
        self._sandbox_dir = tempfile.mkdtemp(dir=str(base), prefix="sandbox_")
        self._provider = LocalProvider(
            sandbox_root=self._sandbox_dir,
            default_timeout=self.timeout,
        )
        return self._provider

    async def post_process(self) -> None:
        """后处理：清理沙箱资源。"""
        if self._sandbox_dir and Path(self._sandbox_dir).exists():
            shutil.rmtree(self._sandbox_dir, ignore_errors=True)
        self._sandbox_dir = None
        self._provider = None
