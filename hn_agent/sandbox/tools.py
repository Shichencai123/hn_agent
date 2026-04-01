"""
沙箱工具：bash, ls, read, write, str_replace。

这些工具封装 SandboxProvider 操作，供 Agent 工具系统调用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hn_agent.sandbox.provider import SandboxProvider


@dataclass
class ToolResult:
    """工具执行结果。"""

    success: bool
    output: str
    error: str = ""


async def bash(provider: SandboxProvider, command: str, timeout: int = 30) -> ToolResult:
    """在沙箱中执行 bash 命令。"""
    try:
        result = await provider.execute(command, language="bash", timeout=timeout)
        return ToolResult(
            success=result.success,
            output=result.stdout,
            error=result.stderr,
        )
    except Exception as exc:
        return ToolResult(success=False, output="", error=str(exc))


async def ls(provider: SandboxProvider, path: str = ".") -> ToolResult:
    """列出沙箱内目录内容。"""
    try:
        files = await provider.list_files(path)
        lines = []
        for f in files:
            prefix = "d" if f.is_dir else "-"
            size_str = f"{f.size:>8}" if not f.is_dir else "       -"
            lines.append(f"{prefix} {size_str}  {f.name}")
        return ToolResult(success=True, output="\n".join(lines))
    except Exception as exc:
        return ToolResult(success=False, output="", error=str(exc))


async def read(provider: SandboxProvider, path: str) -> ToolResult:
    """读取沙箱内文件内容。"""
    try:
        content = await provider.read_file(path)
        return ToolResult(success=True, output=content)
    except Exception as exc:
        return ToolResult(success=False, output="", error=str(exc))


async def write(
    provider: SandboxProvider, path: str, content: str
) -> ToolResult:
    """写入内容到沙箱内文件。"""
    try:
        await provider.write_file(path, content)
        return ToolResult(success=True, output=f"已写入: {path}")
    except Exception as exc:
        return ToolResult(success=False, output="", error=str(exc))


async def str_replace(
    provider: SandboxProvider,
    path: str,
    old_str: str,
    new_str: str,
) -> ToolResult:
    """在沙箱内文件中替换文本。"""
    try:
        content = await provider.read_file(path)
        if old_str not in content:
            return ToolResult(
                success=False,
                output="",
                error=f"未找到要替换的文本: {old_str!r}",
            )
        # 只替换第一次出现
        updated = content.replace(old_str, new_str, 1)
        await provider.write_file(path, updated)
        return ToolResult(success=True, output=f"已替换: {path}")
    except Exception as exc:
        return ToolResult(success=False, output="", error=str(exc))
