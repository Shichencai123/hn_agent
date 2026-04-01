"""上传管理器单元测试。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hn_agent.uploads import (
    CONVERTIBLE_MIME_TYPES,
    FileMetadata,
    UploadFile,
    UploadManager,
)


# ── 测试用 UploadFile 实现 ────────────────────────────────


@dataclass
class FakeUploadFile:
    """模拟 FastAPI UploadFile 的测试替身。"""

    filename: str | None
    content_type: str | None
    _data: bytes = b""

    def read(self) -> bytes:
        return self._data


# ── FileMetadata 数据模型测试 ─────────────────────────────


class TestFileMetadata:
    def test_required_fields(self):
        now = datetime.now(timezone.utc)
        meta = FileMetadata(
            file_id="abc123",
            filename="test.pdf",
            size=1024,
            mime_type="application/pdf",
            upload_time=now,
        )
        assert meta.file_id == "abc123"
        assert meta.filename == "test.pdf"
        assert meta.size == 1024
        assert meta.mime_type == "application/pdf"
        assert meta.upload_time == now
        assert meta.markdown_path is None

    def test_with_markdown_path(self):
        meta = FileMetadata(
            file_id="abc",
            filename="doc.docx",
            size=512,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            upload_time=datetime.now(timezone.utc),
            markdown_path="/data/uploads/t1/abc.md",
        )
        assert meta.markdown_path == "/data/uploads/t1/abc.md"


# ── UploadFile Protocol 兼容性测试 ────────────────────────


class TestUploadFileProtocol:
    def test_fake_upload_file_is_protocol_compliant(self):
        fake = FakeUploadFile(filename="a.txt", content_type="text/plain", _data=b"hi")
        assert isinstance(fake, UploadFile)

    def test_read_returns_bytes(self):
        fake = FakeUploadFile(filename="a.txt", content_type="text/plain", _data=b"hello")
        assert fake.read() == b"hello"


# ── UploadManager 测试 ────────────────────────────────────


class TestUploadManager:
    @pytest.fixture()
    def manager(self, tmp_path: Path) -> UploadManager:
        return UploadManager(base_dir=str(tmp_path / "uploads"))

    # -- 初始化 --

    def test_base_dir(self, tmp_path: Path):
        mgr = UploadManager(base_dir=str(tmp_path / "custom"))
        assert mgr.base_dir == tmp_path / "custom"

    # -- save: 基本功能 --

    def test_save_creates_thread_directory(self, manager: UploadManager):
        fake = FakeUploadFile(filename="hello.txt", content_type="text/plain", _data=b"content")
        manager.save("thread-1", fake)
        assert (manager.base_dir / "thread-1").is_dir()

    def test_save_writes_file(self, manager: UploadManager):
        data = b"file content here"
        fake = FakeUploadFile(filename="note.txt", content_type="text/plain", _data=data)
        meta = manager.save("t1", fake)
        # 文件应存在于线程目录中
        files = list((manager.base_dir / "t1").glob("*"))
        assert len(files) >= 1
        # 至少有一个文件包含原始数据
        found = any(f.read_bytes() == data for f in files)
        assert found

    def test_save_returns_metadata(self, manager: UploadManager):
        fake = FakeUploadFile(filename="doc.txt", content_type="text/plain", _data=b"abc")
        meta = manager.save("t1", fake)
        assert isinstance(meta, FileMetadata)
        assert meta.filename == "doc.txt"
        assert meta.size == 3
        assert meta.mime_type == "text/plain"
        assert meta.file_id  # 非空
        assert meta.upload_time is not None

    def test_save_generates_unique_file_ids(self, manager: UploadManager):
        fake1 = FakeUploadFile(filename="a.txt", content_type="text/plain", _data=b"1")
        fake2 = FakeUploadFile(filename="a.txt", content_type="text/plain", _data=b"2")
        m1 = manager.save("t1", fake1)
        m2 = manager.save("t1", fake2)
        assert m1.file_id != m2.file_id

    def test_save_handles_none_filename(self, manager: UploadManager):
        fake = FakeUploadFile(filename=None, content_type="text/plain", _data=b"x")
        meta = manager.save("t1", fake)
        assert meta.filename.startswith("unnamed_")

    def test_save_handles_none_content_type(self, manager: UploadManager):
        fake = FakeUploadFile(filename="data.json", content_type=None, _data=b"{}")
        meta = manager.save("t1", fake)
        # 应通过文件名猜测 MIME 类型
        assert meta.mime_type  # 非空

    # -- save: 可转换文件（转换失败但保留原始文件） --

    def test_save_convertible_file_keeps_original_on_failure(self, manager: UploadManager):
        """可转换格式的文件，转换失败时保留原始文件，markdown_path 为 None。"""
        fake = FakeUploadFile(
            filename="report.pdf",
            content_type="application/pdf",
            _data=b"%PDF-fake-content",
        )
        meta = manager.save("t1", fake)
        # 转换应失败（NotImplementedError），但原始文件保留
        assert meta.markdown_path is None
        assert meta.size == len(b"%PDF-fake-content")
        # 原始文件存在
        files = list((manager.base_dir / "t1").glob(f"{meta.file_id}_*"))
        assert len(files) == 1

    # -- save: 非可转换文件不尝试转换 --

    def test_save_non_convertible_file_no_markdown(self, manager: UploadManager):
        fake = FakeUploadFile(filename="image.png", content_type="image/png", _data=b"\x89PNG")
        meta = manager.save("t1", fake)
        assert meta.markdown_path is None

    # -- get_metadata --

    def test_get_metadata_returns_saved(self, manager: UploadManager):
        fake = FakeUploadFile(filename="f.txt", content_type="text/plain", _data=b"data")
        saved = manager.save("t1", fake)
        retrieved = manager.get_metadata(saved.file_id)
        assert retrieved is not None
        assert retrieved.file_id == saved.file_id
        assert retrieved.filename == saved.filename

    def test_get_metadata_returns_none_for_unknown(self, manager: UploadManager):
        assert manager.get_metadata("nonexistent") is None

    # -- 多线程目录隔离 --

    def test_files_stored_in_thread_directories(self, manager: UploadManager):
        f1 = FakeUploadFile(filename="a.txt", content_type="text/plain", _data=b"1")
        f2 = FakeUploadFile(filename="b.txt", content_type="text/plain", _data=b"2")
        manager.save("thread-a", f1)
        manager.save("thread-b", f2)
        assert (manager.base_dir / "thread-a").is_dir()
        assert (manager.base_dir / "thread-b").is_dir()
        # 各线程目录只有自己的文件
        a_files = [f.name for f in (manager.base_dir / "thread-a").iterdir()]
        b_files = [f.name for f in (manager.base_dir / "thread-b").iterdir()]
        assert not set(a_files) & set(b_files)


# ── convert_to_markdown 测试 ─────────────────────────────


class TestConvertToMarkdown:
    @pytest.fixture()
    def manager(self, tmp_path: Path) -> UploadManager:
        return UploadManager(base_dir=str(tmp_path))

    def test_file_not_found_raises(self, manager: UploadManager):
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            manager.convert_to_markdown("/nonexistent/file.pdf")

    def test_unsupported_format_raises(self, manager: UploadManager, tmp_path: Path):
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="不支持的文件格式"):
            manager.convert_to_markdown(str(txt_file))

    def test_pdf_raises_not_implemented(self, manager: UploadManager, tmp_path: Path):
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-fake")
        with pytest.raises(NotImplementedError, match="文档转换尚未实现"):
            manager.convert_to_markdown(str(pdf_file))

    def test_docx_raises_not_implemented(self, manager: UploadManager, tmp_path: Path):
        docx_file = tmp_path / "doc.docx"
        docx_file.write_bytes(b"PK-fake")
        with pytest.raises(NotImplementedError, match="文档转换尚未实现"):
            manager.convert_to_markdown(str(docx_file))

    def test_xlsx_raises_not_implemented(self, manager: UploadManager, tmp_path: Path):
        xlsx_file = tmp_path / "data.xlsx"
        xlsx_file.write_bytes(b"PK-fake")
        with pytest.raises(NotImplementedError, match="文档转换尚未实现"):
            manager.convert_to_markdown(str(xlsx_file))

    def test_pptx_raises_not_implemented(self, manager: UploadManager, tmp_path: Path):
        pptx_file = tmp_path / "slides.pptx"
        pptx_file.write_bytes(b"PK-fake")
        with pytest.raises(NotImplementedError, match="文档转换尚未实现"):
            manager.convert_to_markdown(str(pptx_file))


# ── CONVERTIBLE_MIME_TYPES 测试 ──────────────────────────


class TestConvertibleMimeTypes:
    def test_pdf_in_convertible(self):
        assert "application/pdf" in CONVERTIBLE_MIME_TYPES

    def test_docx_in_convertible(self):
        assert (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            in CONVERTIBLE_MIME_TYPES
        )

    def test_xlsx_in_convertible(self):
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in CONVERTIBLE_MIME_TYPES
        )

    def test_pptx_in_convertible(self):
        assert (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            in CONVERTIBLE_MIME_TYPES
        )

    def test_all_values_are_strings(self):
        for mime, fmt in CONVERTIBLE_MIME_TYPES.items():
            assert isinstance(mime, str)
            assert isinstance(fmt, str)
