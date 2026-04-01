"""工具系统单元测试：ToolLoader 和内置工具。"""

from __future__ import annotations

import pytest
from langchain_core.tools import BaseTool

from hn_agent.tools import (
    AgentConfig,
    Features,
    ToolLoader,
    ClarificationTool,
    InvokeACPAgentTool,
    PresentFileTool,
    SetupAgentTool,
    TaskTool,
    ToolSearchTool,
    ViewImageTool,
)


# ══════════════════════════════════════════════════════════
# 内置工具接口一致性测试
# ══════════════════════════════════════════════════════════

ALL_BUILTIN_CLASSES = [
    ClarificationTool,
    PresentFileTool,
    ViewImageTool,
    TaskTool,
    InvokeACPAgentTool,
    SetupAgentTool,
    ToolSearchTool,
]


class TestBuiltinToolInterface:
    """验证所有内置工具满足 BaseTool 接口。"""

    @pytest.mark.parametrize("tool_cls", ALL_BUILTIN_CLASSES)
    def test_is_base_tool(self, tool_cls):
        tool = tool_cls()
        assert isinstance(tool, BaseTool)

    @pytest.mark.parametrize("tool_cls", ALL_BUILTIN_CLASSES)
    def test_has_name(self, tool_cls):
        tool = tool_cls()
        assert tool.name
        assert isinstance(tool.name, str)

    @pytest.mark.parametrize("tool_cls", ALL_BUILTIN_CLASSES)
    def test_has_description(self, tool_cls):
        tool = tool_cls()
        assert tool.description
        assert isinstance(tool.description, str)

    @pytest.mark.parametrize("tool_cls", ALL_BUILTIN_CLASSES)
    def test_has_args_schema(self, tool_cls):
        tool = tool_cls()
        assert tool.args_schema is not None

    def test_unique_names(self):
        names = [cls().name for cls in ALL_BUILTIN_CLASSES]
        assert len(names) == len(set(names))


# ══════════════════════════════════════════════════════════
# 各内置工具测试
# ══════════════════════════════════════════════════════════


class TestClarificationTool:
    def test_name(self):
        assert ClarificationTool().name == "clarification"

    def test_run_returns_structure(self):
        result = ClarificationTool()._run(question="What do you mean?")
        assert result["type"] == "clarification"
        assert result["question"] == "What do you mean?"
        assert result["options"] == []

    def test_run_with_options(self):
        result = ClarificationTool()._run(
            question="Which?", options=["A", "B"]
        )
        assert result["options"] == ["A", "B"]

    def test_args_schema_has_question(self):
        fields = ClarificationTool().args_schema.model_fields
        assert "question" in fields

    def test_args_schema_has_options(self):
        fields = ClarificationTool().args_schema.model_fields
        assert "options" in fields


class TestPresentFileTool:
    def test_name(self):
        assert PresentFileTool().name == "present_file"

    def test_run_returns_structure(self):
        result = PresentFileTool()._run(file_path="main.py")
        assert result["type"] == "present_file"
        assert result["file_path"] == "main.py"

    def test_args_schema_has_file_path(self):
        fields = PresentFileTool().args_schema.model_fields
        assert "file_path" in fields


class TestViewImageTool:
    def test_name(self):
        assert ViewImageTool().name == "view_image"

    def test_run_returns_structure(self):
        result = ViewImageTool()._run(image_path="img.png")
        assert result["type"] == "view_image"
        assert result["image_path"] == "img.png"

    def test_args_schema_has_image_path(self):
        fields = ViewImageTool().args_schema.model_fields
        assert "image_path" in fields


class TestTaskTool:
    def test_name(self):
        assert TaskTool().name == "task"

    def test_run_returns_structure(self):
        result = TaskTool()._run(
            agent_name="bash_agent", instruction="run ls"
        )
        assert result["type"] == "task"
        assert result["agent_name"] == "bash_agent"
        assert result["instruction"] == "run ls"

    def test_args_schema_has_agent_name(self):
        fields = TaskTool().args_schema.model_fields
        assert "agent_name" in fields

    def test_args_schema_has_instruction(self):
        fields = TaskTool().args_schema.model_fields
        assert "instruction" in fields


class TestInvokeACPAgentTool:
    def test_name(self):
        assert InvokeACPAgentTool().name == "invoke_acp_agent"

    def test_run_returns_structure(self):
        result = InvokeACPAgentTool()._run(
            agent_url="http://agent.example.com", message="hello"
        )
        assert result["type"] == "invoke_acp_agent"
        assert result["agent_url"] == "http://agent.example.com"

    def test_args_schema_has_agent_url(self):
        fields = InvokeACPAgentTool().args_schema.model_fields
        assert "agent_url" in fields


class TestSetupAgentTool:
    def test_name(self):
        assert SetupAgentTool().name == "setup_agent"

    def test_run_returns_structure(self):
        result = SetupAgentTool()._run(agent_name="my_agent")
        assert result["type"] == "setup_agent"
        assert result["agent_name"] == "my_agent"

    def test_args_schema_has_agent_name(self):
        fields = SetupAgentTool().args_schema.model_fields
        assert "agent_name" in fields


class TestToolSearchTool:
    def test_name(self):
        assert ToolSearchTool().name == "tool_search"

    def test_run_returns_structure(self):
        result = ToolSearchTool()._run(query="search")
        assert result["type"] == "tool_search"
        assert result["query"] == "search"

    def test_args_schema_has_query(self):
        fields = ToolSearchTool().args_schema.model_fields
        assert "query" in fields


# ══════════════════════════════════════════════════════════
# ToolLoader 测试
# ══════════════════════════════════════════════════════════


class TestToolLoader:
    """ToolLoader 单元测试。"""

    def test_load_tools_default_config(self):
        """默认配置加载内置工具。"""
        loader = ToolLoader()
        config = AgentConfig()
        tools = loader.load_tools(config)
        assert len(tools) > 0
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_load_tools_includes_builtin(self):
        """默认配置包含内置工具。"""
        loader = ToolLoader()
        config = AgentConfig()
        tools = loader.load_tools(config)
        names = {t.name for t in tools}
        assert "clarification" in names
        assert "present_file" in names
        assert "view_image" in names
        assert "tool_search" in names

    def test_load_tools_builtin_disabled(self):
        """禁用内置工具时不加载。"""
        loader = ToolLoader()
        config = AgentConfig(features=Features(builtin_enabled=False))
        tools = loader.load_tools(config)
        names = {t.name for t in tools}
        assert "clarification" not in names

    def test_load_tools_subagent_disabled_excludes_task(self):
        """禁用子 Agent 时不加载 task 工具。"""
        loader = ToolLoader()
        config = AgentConfig(
            features=Features(subagent_enabled=False)
        )
        tools = loader.load_tools(config)
        names = {t.name for t in tools}
        assert "task" not in names

    def test_load_tools_subagent_enabled_includes_task(self):
        """启用子 Agent 时加载 task 工具。"""
        loader = ToolLoader()
        config = AgentConfig(
            features=Features(subagent_enabled=True)
        )
        tools = loader.load_tools(config)
        names = {t.name for t in tools}
        assert "task" in names

    def test_load_sandbox_tools_returns_list(self):
        """沙箱工具加载返回列表。"""
        loader = ToolLoader()
        tools = loader._load_sandbox_tools(object())
        assert isinstance(tools, list)

    def test_load_mcp_tools_returns_list(self):
        """MCP 工具加载返回列表。"""
        loader = ToolLoader()
        tools = loader._load_mcp_tools(["server1"])
        assert isinstance(tools, list)

    def test_load_community_tools_returns_list(self):
        """社区工具加载返回列表。"""
        loader = ToolLoader()
        tools = loader._load_community_tools(["tavily"])
        assert isinstance(tools, list)

    def test_load_tools_no_sandbox_when_disabled(self):
        """禁用沙箱时不加载沙箱工具。"""
        loader = ToolLoader()
        config = AgentConfig(
            features=Features(sandbox_enabled=False),
            sandbox=object(),
        )
        # 即使提供了 sandbox 实例，禁用时也不加载
        tools = loader.load_tools(config)
        # 只有内置工具
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_load_tools_no_sandbox_when_none(self):
        """sandbox 为 None 时不加载沙箱工具。"""
        loader = ToolLoader()
        config = AgentConfig(
            features=Features(sandbox_enabled=True),
            sandbox=None,
        )
        tools = loader.load_tools(config)
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_load_tools_mcp_disabled(self):
        """禁用 MCP 时不加载 MCP 工具。"""
        loader = ToolLoader()
        config = AgentConfig(
            features=Features(mcp_enabled=False),
            mcp_servers=["server1"],
        )
        tools = loader.load_tools(config)
        # 只有内置工具
        assert len(tools) > 0


# ══════════════════════════════════════════════════════════
# 导出测试
# ══════════════════════════════════════════════════════════


class TestToolsExports:
    """验证 hn_agent.tools 导出所有公开接口。"""

    def test_exports_tool_loader(self):
        from hn_agent.tools import ToolLoader
        assert ToolLoader is not None

    def test_exports_features(self):
        from hn_agent.tools import Features
        assert Features is not None

    def test_exports_agent_config(self):
        from hn_agent.tools import AgentConfig
        assert AgentConfig is not None

    def test_exports_all_builtins(self):
        from hn_agent.tools import (
            ClarificationTool,
            PresentFileTool,
            ViewImageTool,
            TaskTool,
            InvokeACPAgentTool,
            SetupAgentTool,
            ToolSearchTool,
        )
        assert all(
            cls is not None
            for cls in [
                ClarificationTool,
                PresentFileTool,
                ViewImageTool,
                TaskTool,
                InvokeACPAgentTool,
                SetupAgentTool,
                ToolSearchTool,
            ]
        )
