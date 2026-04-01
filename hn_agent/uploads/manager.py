"""
上传管理器：文件存储、元数据管理和文档格式转换。
"""

from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# 支持转换的 MIME 类型映射
CONVERTIBLE_MIME_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}


@dataclass
class FileMetadata:
    """上传文件的元数据。"""

    file_id: str
    filename: str
    size: int
    mime_type: str
    upload_time: datetime
    markdown_path: str | None = None


@runtime_checkable
class UploadFile(Protocol):
    """上传文件协议，兼容 FastAPI UploadFile 接口。"""

    filename: str | None
    content_type: str | None

    def read(self) -> bytes: ...


class UploadManager:
    """管理文件上传、存储和文档格式转换。"""

    def __init__(self, base_dir: str = "./data/uploads") -> None:
        self._base_dir = Path(base_dir)
        self._metadata_store: dict[str, FileMetadata] = {}

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def save(self, thread_id: str, file: UploadFile) -> FileMetadata:
        """保存上传文件到线程关联目录，返回文件元数据。"""
        file_id = uuid.uuid4().hex
        filename = file.filename or f"unnamed_{file_id}"
        content = file.read()
        size = len(content)
        mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # 创建线程目录
        thread_dir = self._base_dir / thread_id
        thread_dir.mkdir(parents=True, exist_ok=True)

        # 写入文件：使用 file_id 前缀避免文件名冲突
        dest_path = thread_dir / f"{file_id}_{filename}"
        dest_path.write_bytes(content)

        # 尝试转换为 Markdown
        markdown_path: str | None = None
        if mime_type in CONVERTIBLE_MIME_TYPES:
            try:
                md_content = self.convert_to_markdown(str(dest_path))
                md_dest = thread_dir / f"{file_id}.md"
                md_dest.write_text(md_content, encoding="utf-8")
                markdown_path = str(md_dest)
            except (NotImplementedError, Exception) as exc:
                logger.error(
                    "文件格式转换失败: file_id=%s, filename=%s, error=%s",
                    file_id,
                    filename,
                    exc,
                )
                # 保留原始文件，markdown_path 为 None

        metadata = FileMetadata(
            file_id=file_id,
            filename=filename,
            size=size,
            mime_type=mime_type,
            upload_time=datetime.now(timezone.utc),
            markdown_path=markdown_path,
        )
        self._metadata_store[file_id] = metadata
        return metadata

    def convert_to_markdown(self, file_path: str) -> str:
        """将文档文件转换为 Markdown 格式。

        当前为桩实现，实际转换库（pypdf, python-pptx, openpyxl, python-docx）
        可在后续集成。

        Raises:
            NotImplementedError: 转换库尚未集成。
            FileNotFoundError: 文件不存在。
            ValueError: 不支持的文件格式。
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        mime_type = mimetypes.guess_type(file_path)[0] or ""
        suffix = path.suffix.lower()

        # 检查是否为支持的格式
        supported_suffixes = {".pdf", ".pptx", ".ppt", ".xlsx", ".xls", ".docx", ".doc"}
        if suffix not in supported_suffixes and mime_type not in CONVERTIBLE_MIME_TYPES:
            raise ValueError(f"不支持的文件格式: {suffix} (mime: {mime_type})")

        fmt = CONVERTIBLE_MIME_TYPES.get(mime_type, suffix.lstrip("."))
        raise NotImplementedError(
            f"文档转换尚未实现: 格式={fmt}, 文件={path.name}。"
            f"需要集成对应的转换库。"
        )

    def get_metadata(self, file_id: str) -> FileMetadata | None:
        """根据 file_id 获取文件元数据，不存在返回 None。"""
        return self._metadata_store.get(file_id)
