"""
内置工具：view_image — 查看图片。
"""

from __future__ import annotations

from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ViewImageInput(BaseModel):
    """图片查看工具的输入参数。"""

    image_path: str = Field(description="图片文件路径或 URL")
    alt_text: str = Field(default="", description="图片替代文本描述")


class ViewImageTool(BaseTool):
    """查看图片的工具。"""

    name: str = "view_image"
    description: str = "查看指定路径或 URL 的图片，将图片数据注入到线程状态中。"
    args_schema: Type[BaseModel] = ViewImageInput

    def _run(self, image_path: str, alt_text: str = "") -> Any:
        """桩实现：返回图片查看请求结构。"""
        return {
            "type": "view_image",
            "image_path": image_path,
            "alt_text": alt_text,
        }
