"""
内置工具：present_file — 向用户展示文件内容。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class PresentFileInput(BaseModel):
    """文件展示工具的输入参数。"""

    file_path: str = Field(description="要展示的文件路径")
    language: str = Field(default="", description="文件语言（用于语法高亮）")
    start_line: int | None = Field(default=None, description="起始行号")
    end_line: int | None = Field(default=None, description="结束行号")


class PresentFileTool(BaseTool):
    """向用户展示文件内容的工具。"""

    name: str = "present_file"
    description: str = "向用户展示指定文件的内容，支持指定行范围和语法高亮。"
    args_schema: Type[BaseModel] = PresentFileInput

    def _run(
        self,
        file_path: str,
        language: str = "",
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> Any:
        """桩实现：返回文件展示请求结构。"""
        return {
            "type": "present_file",
            "file_path": file_path,
            "language": language,
            "start_line": start_line,
            "end_line": end_line,
        }
