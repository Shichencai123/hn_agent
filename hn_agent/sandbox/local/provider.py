"""
LocalProvider：本地文件系统隔离目录中执行代码。

在临时目录中运行子进程，通过 path_translator 防止路径逃逸。
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from hn_agent.exceptions import PathEscapeError, SandboxTimeoutError
from hn_agent.sandbox.path_translator import translate_path
from hn_agent.sandbox.provider import ExecutionResult, FileInfo


class LocalProvider:
    """本地文件系统沙箱 Provider。"""

    def __init__(self, sandbox_root: str, default_timeout: int = 30) -> None:
        self.sandbox_root = str(Path(sandbox_root).resolve())
        self.default_timeout = default_timeout
        # 确保沙箱根目录存在
        Path(self.sandbox_root).mkdir(parents=True, exist_ok=True)

    async def execute(
        self, code: str, language: str, timeout: int | None = None
    ) -> ExecutionResult:
        """在沙箱目录中执行代码。"""
        timeout = timeout if timeout is not None else self.default_timeout

        if language == "python":
            cmd = ["python", "-c", code]
        elif language == "bash":
            cmd = ["bash", "-c", code]
        else:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"不支持的语言: {language}",
                exit_code=1,
                duration=0.0,
            )

        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.sandbox_root,
                env={**os.environ, "HOME": self.sandbox_root},
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            duration = time.monotonic() - start
            exit_code = proc.returncode or 0
            return ExecutionResult(
                success=exit_code == 0,
                stdout=stdout_bytes.decode(errors="replace"),
                stderr=stderr_bytes.decode(errors="replace"),
                exit_code=exit_code,
                duration=duration,
            )
        except asyncio.TimeoutError:
            duration = time.monotonic() - start
            # 尝试终止进程
            try:
                proc.kill()  # type: ignore[possibly-undefined]
                await proc.wait()  # type: ignore[possibly-undefined]
            except Exception:
                pass
            raise SandboxTimeoutError(
                f"执行超时 ({timeout}s)"
            )
        except Exception as exc:
            duration = time.monotonic() - start
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                duration=duration,
            )

    async def read_file(self, virtual_path: str) -> str:
        """读取沙箱内文件。"""
        real_path = translate_path(virtual_path, self.sandbox_root)
        path = Path(real_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {virtual_path}")
        if not path.is_file():
            raise IsADirectoryError(f"路径是目录: {virtual_path}")
        return path.read_text(encoding="utf-8")

    async def write_file(self, virtual_path: str, content: str) -> None:
        """写入内容到沙箱内文件。"""
        real_path = translate_path(virtual_path, self.sandbox_root)
        path = Path(real_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    async def list_files(self, virtual_path: str = ".") -> list[FileInfo]:
        """列出沙箱内目录内容。"""
        real_path = translate_path(virtual_path, self.sandbox_root)
        path = Path(real_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {virtual_path}")
        if not path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {virtual_path}")

        result: list[FileInfo] = []
        for entry in sorted(path.iterdir()):
            try:
                stat = entry.stat()
                # 确保列出的文件也在沙箱内
                entry.resolve().relative_to(Path(self.sandbox_root).resolve())
                result.append(
                    FileInfo(
                        name=entry.name,
                        path=str(entry.relative_to(Path(self.sandbox_root))),
                        is_dir=entry.is_dir(),
                        size=stat.st_size if entry.is_file() else 0,
                    )
                )
            except (ValueError, OSError):
                # 跳过逃逸的符号链接或无法访问的文件
                continue
        return result
