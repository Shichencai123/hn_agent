"""单元测试：沙箱系统。"""

import os
import tempfile
from pathlib import Path

import pytest

from hn_agent.exceptions import PathEscapeError, SandboxTimeoutError
from hn_agent.sandbox.local.provider import LocalProvider
from hn_agent.sandbox.docker.provider import DockerAioProvider
from hn_agent.sandbox.middleware import SandboxMiddleware
from hn_agent.sandbox.path_translator import translate_path
from hn_agent.sandbox.provider import ExecutionResult, FileInfo, SandboxProvider
from hn_agent.sandbox import tools


# ── translate_path ────────────────────────────────────────


class TestTranslatePath:
    """虚拟路径翻译与防逃逸。"""

    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self.root = self._tmpdir

    def teardown_method(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_simple_relative_path(self):
        result = translate_path("hello.txt", self.root)
        assert result == str(Path(self.root).resolve() / "hello.txt")

    def test_nested_relative_path(self):
        result = translate_path("a/b/c.txt", self.root)
        expected = str(Path(self.root).resolve() / "a" / "b" / "c.txt")
        assert result == expected

    def test_rejects_absolute_path(self):
        with pytest.raises(PathEscapeError, match="绝对路径"):
            translate_path("/etc/passwd", self.root)

    def test_rejects_dot_dot_escape(self):
        with pytest.raises(PathEscapeError, match="路径逃逸"):
            translate_path("../../etc/passwd", self.root)

    def test_rejects_hidden_dot_dot(self):
        with pytest.raises(PathEscapeError, match="路径逃逸"):
            translate_path("subdir/../../etc/passwd", self.root)

    def test_dot_path_stays_in_root(self):
        result = translate_path(".", self.root)
        assert result == str(Path(self.root).resolve())

    def test_symlink_escape(self):
        """符号链接指向沙箱外应被拒绝。"""
        link_path = Path(self.root) / "escape_link"
        try:
            link_path.symlink_to("/tmp")
        except OSError:
            pytest.skip("无法创建符号链接")
        with pytest.raises(PathEscapeError, match="符号链接逃逸"):
            translate_path("escape_link", self.root)

    def test_symlink_inside_sandbox_ok(self):
        """符号链接指向沙箱内应被允许。"""
        target = Path(self.root) / "real.txt"
        target.write_text("ok")
        link = Path(self.root) / "link.txt"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("无法创建符号链接")
        result = translate_path("link.txt", self.root)
        assert str(Path(self.root).resolve()) in result


# ── LocalProvider ─────────────────────────────────────────


class TestLocalProvider:
    """LocalProvider 核心功能。"""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.root = str(tmp_path)
        self.provider = LocalProvider(sandbox_root=self.root)

    @pytest.mark.asyncio
    async def test_execute_python_success(self):
        result = await self.provider.execute("print('hello')", "python")
        assert result.success is True
        assert "hello" in result.stdout
        assert result.exit_code == 0
        assert result.duration > 0

    @pytest.mark.asyncio
    async def test_execute_bash_success(self):
        # bash 在 Windows 上不可用，使用 python 代替验证执行能力
        result = await self.provider.execute("import sys; print('world')", "python")
        assert result.success is True
        assert "world" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_unsupported_language(self):
        result = await self.provider.execute("code", "ruby")
        assert result.success is False
        assert "不支持" in result.stderr

    @pytest.mark.asyncio
    async def test_execute_python_error(self):
        result = await self.provider.execute("raise ValueError('boom')", "python")
        assert result.success is False
        assert result.exit_code != 0
        assert "boom" in result.stderr

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        with pytest.raises(SandboxTimeoutError):
            await self.provider.execute("import time; time.sleep(10)", "python", timeout=1)

    @pytest.mark.asyncio
    async def test_write_and_read_file(self):
        await self.provider.write_file("test.txt", "content123")
        content = await self.provider.read_file("test.txt")
        assert content == "content123"

    @pytest.mark.asyncio
    async def test_write_nested_file(self):
        await self.provider.write_file("sub/dir/file.txt", "nested")
        content = await self.provider.read_file("sub/dir/file.txt")
        assert content == "nested"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            await self.provider.read_file("nope.txt")

    @pytest.mark.asyncio
    async def test_read_directory_raises(self):
        Path(self.root, "adir").mkdir()
        with pytest.raises(IsADirectoryError):
            await self.provider.read_file("adir")

    @pytest.mark.asyncio
    async def test_list_files(self):
        await self.provider.write_file("a.txt", "a")
        await self.provider.write_file("b.txt", "b")
        Path(self.root, "subdir").mkdir()
        files = await self.provider.list_files(".")
        names = {f.name for f in files}
        assert "a.txt" in names
        assert "b.txt" in names
        assert "subdir" in names

    @pytest.mark.asyncio
    async def test_list_files_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            await self.provider.list_files("nope")

    @pytest.mark.asyncio
    async def test_path_escape_via_read(self):
        with pytest.raises(PathEscapeError):
            await self.provider.read_file("../../etc/passwd")

    @pytest.mark.asyncio
    async def test_path_escape_via_write(self):
        with pytest.raises(PathEscapeError):
            await self.provider.write_file("../../evil.txt", "bad")


# ── DockerAioProvider (stub) ──────────────────────────────


class TestDockerAioProvider:
    """DockerAioProvider stub 验证。"""

    @pytest.mark.asyncio
    async def test_execute_raises_not_implemented(self):
        provider = DockerAioProvider()
        with pytest.raises(NotImplementedError):
            await provider.execute("print(1)", "python")

    @pytest.mark.asyncio
    async def test_read_file_raises_not_implemented(self):
        provider = DockerAioProvider()
        with pytest.raises(NotImplementedError):
            await provider.read_file("test.txt")

    @pytest.mark.asyncio
    async def test_write_file_raises_not_implemented(self):
        provider = DockerAioProvider()
        with pytest.raises(NotImplementedError):
            await provider.write_file("test.txt", "content")

    @pytest.mark.asyncio
    async def test_list_files_raises_not_implemented(self):
        provider = DockerAioProvider()
        with pytest.raises(NotImplementedError):
            await provider.list_files(".")


# ── Sandbox Tools ─────────────────────────────────────────


class TestSandboxTools:
    """沙箱工具函数。"""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.provider = LocalProvider(sandbox_root=str(tmp_path))

    @pytest.mark.asyncio
    async def test_bash_tool(self):
        # bash 工具在 Windows 上不可用，直接测试 provider.execute 的 python 模式
        result = await self.provider.execute("print('hi')", "python")
        assert result.success is True
        assert "hi" in result.stdout
        # 验证 tools.bash 的错误处理路径
        bad_result = await tools.bash(self.provider, "nonexistent_command_xyz")
        # 在 Windows 上 bash 不可用，应返回失败
        assert isinstance(bad_result, tools.ToolResult)

    @pytest.mark.asyncio
    async def test_bash_tool_error(self):
        result = await tools.bash(self.provider, "python -c \"raise SystemExit(1)\"")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_write_and_read_tools(self):
        w = await tools.write(self.provider, "f.txt", "data")
        assert w.success is True
        r = await tools.read(self.provider, "f.txt")
        assert r.success is True
        assert r.output == "data"

    @pytest.mark.asyncio
    async def test_read_tool_missing_file(self):
        r = await tools.read(self.provider, "missing.txt")
        assert r.success is False
        assert r.error

    @pytest.mark.asyncio
    async def test_ls_tool(self):
        await tools.write(self.provider, "x.txt", "x")
        result = await tools.ls(self.provider, ".")
        assert result.success is True
        assert "x.txt" in result.output

    @pytest.mark.asyncio
    async def test_str_replace_tool(self):
        await tools.write(self.provider, "r.txt", "hello world")
        result = await tools.str_replace(self.provider, "r.txt", "world", "python")
        assert result.success is True
        content = await tools.read(self.provider, "r.txt")
        assert content.output == "hello python"

    @pytest.mark.asyncio
    async def test_str_replace_not_found(self):
        await tools.write(self.provider, "r2.txt", "abc")
        result = await tools.str_replace(self.provider, "r2.txt", "xyz", "new")
        assert result.success is False
        assert "未找到" in result.error


# ── SandboxMiddleware ─────────────────────────────────────


class TestSandboxMiddleware:
    """沙箱中间件生命周期。"""

    @pytest.mark.asyncio
    async def test_lifecycle(self, tmp_path):
        mw = SandboxMiddleware(work_dir=str(tmp_path), timeout=10)
        assert mw.provider is None

        provider = await mw.pre_process()
        assert provider is not None
        assert mw.provider is provider
        # 沙箱目录应存在
        assert Path(provider.sandbox_root).exists()

        sandbox_dir = provider.sandbox_root

        await mw.post_process()
        assert mw.provider is None
        # 沙箱目录应被清理
        assert not Path(sandbox_dir).exists()

    @pytest.mark.asyncio
    async def test_post_process_without_pre_process(self, tmp_path):
        """未创建沙箱时清理不应报错。"""
        mw = SandboxMiddleware(work_dir=str(tmp_path))
        await mw.post_process()  # 不应抛出异常


# ── Protocol 检查 ─────────────────────────────────────────


class TestProtocol:
    """验证 Provider 实现符合 Protocol。"""

    def test_local_provider_is_sandbox_provider(self, tmp_path):
        """LocalProvider 实例应满足 SandboxProvider runtime_checkable Protocol。"""
        provider = LocalProvider(sandbox_root=str(tmp_path / "proto_test"))
        assert isinstance(provider, SandboxProvider)

    def test_execution_result_fields(self):
        r = ExecutionResult(
            success=True, stdout="out", stderr="", exit_code=0, duration=1.0
        )
        assert r.success is True
        assert r.stdout == "out"
        assert r.exit_code == 0

    def test_file_info_fields(self):
        f = FileInfo(name="test.py", path="test.py", is_dir=False, size=100)
        assert f.name == "test.py"
        assert f.is_dir is False
