"""
沙箱 Provider 协议与核心数据模型。

定义 SandboxProvider Protocol 和 ExecutionResult / FileInfo 数据类。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ExecutionResult:
    """代码执行结果。"""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration: float


@dataclass
class FileInfo:
    """文件/目录信息。"""

    name: str
    path: str
    is_dir: bool
    size: int = 0


@runtime_checkable
class SandboxProvider(Protocol):
    """沙箱 Provider 抽象接口。"""

    async def execute(
        self, code: str, language: str, timeout: int = 30
    ) -> ExecutionResult:
        """在沙箱中执行代码。"""
        ...

    async def read_file(self, virtual_path: str) -> str:
        """读取沙箱内文件内容。"""
        ...

    async def write_file(self, virtual_path: str, content: str) -> None:
        """写入内容到沙箱内文件。"""
        ...

    async def list_files(self, virtual_path: str = ".") -> list[FileInfo]:
        """列出沙箱内目录内容。"""
        ...
