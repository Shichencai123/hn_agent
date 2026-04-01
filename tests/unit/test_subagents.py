"""
子 Agent 系统单元测试。

覆盖：SubagentDefinition, SubagentTask, SubagentResult 数据模型、
SubagentRegistry 注册表、SubagentExecutor 执行器、内置子 Agent。
"""

from __future__ import annotations

import pytest

from hn_agent.subagents.config import (
    SubagentDefinition,
    SubagentResult,
    SubagentTask,
    TaskType,
)
from hn_agent.subagents.executor import SubagentExecutor
from hn_agent.subagents.registry import SubagentRegistry


# ── 数据模型测试 ──────────────────────────────────────────


class TestSubagentDefinition:
    def test_create_with_defaults(self):
        defn = SubagentDefinition(name="test", description="A test agent")
        assert defn.name == "test"
        assert defn.description == "A test agent"
        assert defn.task_type == TaskType.IO
        assert defn.metadata == {}

    def test_create_with_cpu_type(self):
        defn = SubagentDefinition(
            name="cpu_agent", description="CPU agent", task_type=TaskType.CPU
        )
        assert defn.task_type == TaskType.CPU

    def test_metadata(self):
        defn = SubagentDefinition(
            name="m", description="d", metadata={"key": "value"}
        )
        assert defn.metadata["key"] == "value"


class TestSubagentTask:
    def test_create_with_required_fields(self):
        task = SubagentTask(
            task_id="t1",
            agent_name="agent",
            instruction="do something",
            parent_thread_id="thread-1",
        )
        assert task.task_id == "t1"
        assert task.agent_name == "agent"
        assert task.instruction == "do something"
        assert task.parent_thread_id == "thread-1"
        assert task.context == {}

    def test_create_with_context(self):
        task = SubagentTask(
            task_id="t2",
            agent_name="agent",
            instruction="do",
            parent_thread_id="th",
            context={"data": 42},
        )
        assert task.context["data"] == 42

    def test_factory_method(self):
        task = SubagentTask.create(
            agent_name="agent",
            instruction="hello",
            parent_thread_id="thread-1",
        )
        assert task.task_id  # 非空
        assert len(task.task_id) == 32  # uuid4 hex
        assert task.agent_name == "agent"

    def test_factory_method_with_context(self):
        task = SubagentTask.create(
            agent_name="a",
            instruction="i",
            parent_thread_id="t",
            context={"k": "v"},
        )
        assert task.context == {"k": "v"}

    def test_factory_generates_unique_ids(self):
        t1 = SubagentTask.create("a", "i", "t")
        t2 = SubagentTask.create("a", "i", "t")
        assert t1.task_id != t2.task_id


class TestSubagentResult:
    def test_success_result(self):
        result = SubagentResult(task_id="t1", success=True, output="done")
        assert result.success is True
        assert result.output == "done"
        assert result.error is None

    def test_failure_result(self):
        result = SubagentResult(
            task_id="t1", success=False, output="", error="boom"
        )
        assert result.success is False
        assert result.error == "boom"


class TestTaskType:
    def test_io_value(self):
        assert TaskType.IO.value == "io"

    def test_cpu_value(self):
        assert TaskType.CPU.value == "cpu"


# ── 注册表测试 ────────────────────────────────────────────


class TestSubagentRegistry:
    def test_register_and_get(self):
        registry = SubagentRegistry()
        defn = SubagentDefinition(name="test", description="desc")
        registry.register("test", defn)
        assert registry.get("test") is defn

    def test_get_nonexistent_returns_none(self):
        registry = SubagentRegistry()
        assert registry.get("nonexistent") is None

    def test_register_empty_name_raises(self):
        registry = SubagentRegistry()
        defn = SubagentDefinition(name="", description="d")
        with pytest.raises(ValueError, match="不能为空"):
            registry.register("", defn)

    def test_overwrite_existing(self):
        registry = SubagentRegistry()
        d1 = SubagentDefinition(name="a", description="first")
        d2 = SubagentDefinition(name="a", description="second")
        registry.register("a", d1)
        registry.register("a", d2)
        assert registry.get("a") is d2

    def test_list_agents(self):
        registry = SubagentRegistry()
        registry.register("a", SubagentDefinition(name="a", description=""))
        registry.register("b", SubagentDefinition(name="b", description=""))
        names = registry.list_agents()
        assert set(names) == {"a", "b"}

    def test_len(self):
        registry = SubagentRegistry()
        assert len(registry) == 0
        registry.register("x", SubagentDefinition(name="x", description=""))
        assert len(registry) == 1

    def test_contains(self):
        registry = SubagentRegistry()
        registry.register("x", SubagentDefinition(name="x", description=""))
        assert "x" in registry
        assert "y" not in registry

    def test_iter(self):
        registry = SubagentRegistry()
        registry.register("a", SubagentDefinition(name="a", description=""))
        registry.register("b", SubagentDefinition(name="b", description=""))
        assert set(registry) == {"a", "b"}


# ── 执行器测试 ────────────────────────────────────────────


class TestSubagentExecutor:
    @pytest.fixture(autouse=True)
    def _executor(self):
        self.executor = SubagentExecutor(io_workers=1, cpu_workers=1)
        yield
        self.executor.shutdown(wait=True)

    @pytest.mark.asyncio
    async def test_submit_and_get_result(self):
        self.executor.register_handler("echo", lambda t: f"echo: {t.instruction}")
        task = SubagentTask.create("echo", "hello", "thread-1")
        task_id = await self.executor.submit(task)
        result = await self.executor.get_result(task_id)
        assert result.success is True
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_submit_unregistered_agent_raises(self):
        task = SubagentTask.create("unknown", "hello", "thread-1")
        with pytest.raises(ValueError, match="未注册"):
            await self.executor.submit(task)

    @pytest.mark.asyncio
    async def test_error_captured_in_result(self):
        def failing_handler(task: SubagentTask) -> str:
            raise RuntimeError("intentional error")

        self.executor.register_handler("fail", failing_handler)
        task = SubagentTask.create("fail", "boom", "thread-1")
        task_id = await self.executor.submit(task)
        result = await self.executor.get_result(task_id)
        assert result.success is False
        assert result.error is not None
        assert "intentional error" in result.error

    @pytest.mark.asyncio
    async def test_cpu_pool_submission(self):
        self.executor.register_handler("cpu_task", lambda t: "cpu done")
        task = SubagentTask.create("cpu_task", "compute", "thread-1")
        task_id = await self.executor.submit(task, task_type=TaskType.CPU)
        result = await self.executor.get_result(task_id)
        assert result.success is True
        assert result.output == "cpu done"

    @pytest.mark.asyncio
    async def test_get_result_unknown_task_raises(self):
        with pytest.raises(KeyError, match="未知的任务 ID"):
            await self.executor.get_result("nonexistent")

    @pytest.mark.asyncio
    async def test_get_result_from_cache(self):
        """已完成的任务结果应可从缓存中重复获取。"""
        self.executor.register_handler("echo", lambda t: "cached")
        task = SubagentTask.create("echo", "test", "thread-1")
        task_id = await self.executor.submit(task)
        r1 = await self.executor.get_result(task_id)
        # 第二次从 _results 缓存获取
        r2 = await self.executor.get_result(task_id)
        assert r1.task_id == r2.task_id
        assert r1.success is True


# ── 内置子 Agent 测试 ─────────────────────────────────────


class TestBuiltinSubagents:
    def test_general_purpose_definition(self):
        from hn_agent.subagents.builtins import GENERAL_PURPOSE_DEF

        assert GENERAL_PURPOSE_DEF.name == "general_purpose"
        assert GENERAL_PURPOSE_DEF.description
        assert GENERAL_PURPOSE_DEF.task_type == TaskType.IO

    def test_bash_agent_definition(self):
        from hn_agent.subagents.builtins import BASH_AGENT_DEF

        assert BASH_AGENT_DEF.name == "bash_agent"
        assert BASH_AGENT_DEF.description
        assert BASH_AGENT_DEF.task_type == TaskType.IO

    def test_general_purpose_handler(self):
        from hn_agent.subagents.builtins import general_purpose_handler

        task = SubagentTask.create("general_purpose", "do stuff", "thread-1")
        result = general_purpose_handler(task)
        assert "do stuff" in result
        assert "thread-1" in result

    def test_bash_agent_handler(self):
        from hn_agent.subagents.builtins import bash_agent_handler

        task = SubagentTask.create("bash_agent", "ls -la", "thread-2")
        result = bash_agent_handler(task)
        assert "ls -la" in result
        assert "thread-2" in result


# ── 导出测试 ──────────────────────────────────────────────


class TestSubagentsExports:
    def test_exports_registry(self):
        from hn_agent.subagents import SubagentRegistry

        assert SubagentRegistry is not None

    def test_exports_executor(self):
        from hn_agent.subagents import SubagentExecutor

        assert SubagentExecutor is not None

    def test_exports_definition(self):
        from hn_agent.subagents import SubagentDefinition

        assert SubagentDefinition is not None

    def test_exports_task(self):
        from hn_agent.subagents import SubagentTask

        assert SubagentTask is not None

    def test_exports_result(self):
        from hn_agent.subagents import SubagentResult

        assert SubagentResult is not None

    def test_exports_task_type(self):
        from hn_agent.subagents import TaskType

        assert TaskType is not None
