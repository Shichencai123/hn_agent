"""
DockerAioProvider：Docker 容器中执行代码（placeholder/stub）。

完整实现将在后续迭代中完成。
"""

from __future__ import annotations

from hn_agent.sandbox.provider import ExecutionResult, FileInfo


class DockerAioProvider:
    """Docker 容器沙箱 Provider（stub 实现）。"""

    def __init__(
        self,
        image: str = "python:3.12-slim",
        default_timeout: int = 30,
    ) -> None:
        self.image = image
        self.default_timeout = default_timeout

    async def execute(
        self, code: str, language: str, timeout: int | None = None
    ) -> ExecutionResult:
        """在 Docker 容器中执行代码（stub）。"""
        raise NotImplementedError("DockerAioProvider 尚未实现")

    async def read_file(self, virtual_path: str) -> str:
        """读取容器内文件（stub）。"""
        raise NotImplementedError("DockerAioProvider 尚未实现")

    async def write_file(self, virtual_path: str, content: str) -> None:
        """写入内容到容器内文件（stub）。"""
        raise NotImplementedError("DockerAioProvider 尚未实现")

    async def list_files(self, virtual_path: str = ".") -> list[FileInfo]:
        """列出容器内目录内容（stub）。"""
        raise NotImplementedError("DockerAioProvider 尚未实现")
