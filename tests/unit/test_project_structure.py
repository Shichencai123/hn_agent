"""单元测试：项目结构和公开接口。"""

import importlib
from pathlib import Path

import pytest


class TestPackageStructure:
    """验证 hn_agent 包结构和公开接口导出。"""

    EXPECTED_SUBMODULES = [
        "agents",
        "sandbox",
        "tools",
        "models",
        "mcp",
        "skills",
        "config",
        "guardrails",
        "memory",
        "subagents",
        "reflection",
        "client",
    ]

    def test_hn_agent_package_importable(self):
        mod = importlib.import_module("hn_agent")
        assert mod is not None

    @pytest.mark.parametrize("submodule", EXPECTED_SUBMODULES)
    def test_submodule_importable(self, submodule):
        mod = importlib.import_module(f"hn_agent.{submodule}")
        assert mod is not None

    def test_init_exports_all_submodules(self):
        import hn_agent

        for name in self.EXPECTED_SUBMODULES:
            assert hasattr(hn_agent, name), f"hn_agent 缺少导出: {name}"

    def test_exceptions_module_importable(self):
        from hn_agent.exceptions import HarnessError

        assert issubclass(HarnessError, Exception)


class TestDirectoryStructure:
    """验证关键目录存在。"""

    @pytest.mark.parametrize(
        "path",
        [
            "hn_agent",
            "app",
            "app/gateway",
            "app/channels",
            "tests/unit",
            "tests/properties",
            "tests/integration",
        ],
    )
    def test_directory_exists(self, path):
        assert Path(path).is_dir(), f"目录不存在: {path}"
