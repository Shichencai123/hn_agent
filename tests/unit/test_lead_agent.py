"""Lead Agent 核心单元测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from hn_agent.agents.lead_agent.prompt import build_system_prompt, _BASE_PROMPT
from hn_agent.agents.lead_agent.agent import create_lead_agent
from hn_agent.agents.factory import AgentConfig
from hn_agent.agents.features import Features
from hn_agent.skills.types import Skill


# ── build_system_prompt 测试 ─────────────────────────────


class TestBuildSystemPrompt:
    def _make_config(self, **kwargs) -> AgentConfig:
        return AgentConfig(**kwargs)

    def test_basic_prompt_contains_base(self):
        config = self._make_config(name="TestAgent", model_name="gpt-4o")
        result = build_system_prompt(config)
        assert _BASE_PROMPT in result
        assert "TestAgent" in result
        assert "gpt-4o" in result

    def test_prompt_includes_skill_prompts(self):
        config = self._make_config(name="Agent", model_name="gpt-4o")
        skills = [
            Skill(name="search", description="搜索", prompt="你可以搜索互联网"),
            Skill(name="code", description="编码", prompt="你可以编写代码"),
        ]
        result = build_system_prompt(config, skills=skills)
        assert "你可以搜索互联网" in result
        assert "你可以编写代码" in result
        assert "<skills>" in result
        assert "### 技能: search" in result
        assert "### 技能: code" in result

    def test_prompt_includes_memory_context(self):
        config = self._make_config(name="Agent", model_name="gpt-4o")
        memory = "用户喜欢 Python 编程"
        result = build_system_prompt(config, memory_context=memory)
        assert "用户喜欢 Python 编程" in result

    def test_empty_skills_no_skills_section(self):
        config = self._make_config(name="Agent", model_name="gpt-4o")
        result = build_system_prompt(config, skills=[])
        assert "<skills>" not in result

    def test_skill_with_empty_prompt_skipped(self):
        config = self._make_config(name="Agent", model_name="gpt-4o")
        skills = [
            Skill(name="empty", description="空", prompt=""),
            Skill(name="valid", description="有效", prompt="有效提示词"),
        ]
        result = build_system_prompt(config, skills=skills)
        assert "有效提示词" in result
        assert "### 技能: empty" not in result

    def test_empty_memory_not_included(self):
        config = self._make_config(name="Agent", model_name="gpt-4o")
        result = build_system_prompt(config, memory_context="")
        # 只有基础提示词部分
        sections = result.split("\n\n")
        # 不应有空的记忆段
        assert all(s.strip() for s in sections)

    def test_all_sections_combined(self):
        config = self._make_config(name="SuperAgent", model_name="claude-3-opus")
        skills = [Skill(name="s1", description="d1", prompt="技能1内容")]
        memory = "记忆上下文内容"
        result = build_system_prompt(config, skills=skills, memory_context=memory)
        assert "SuperAgent" in result
        assert "claude-3-opus" in result
        assert "技能1内容" in result
        assert "记忆上下文内容" in result


# ── create_lead_agent 测试 ───────────────────────────────


class TestCreateLeadAgent:
    @patch("hn_agent.agents.lead_agent.agent.create_react_agent")
    def test_creates_agent_with_correct_args(self, mock_create):
        mock_graph = MagicMock(spec=CompiledStateGraph)
        mock_create.return_value = mock_graph

        model = MagicMock(spec=BaseChatModel)
        tools = [MagicMock(spec=BaseTool)]
        prompt = "test prompt"

        result = create_lead_agent(model, tools, prompt)

        assert result is mock_graph
        mock_create.assert_called_once_with(
            model=model,
            tools=tools,
            prompt=prompt,
            checkpointer=None,
        )

    @patch("hn_agent.agents.lead_agent.agent.create_react_agent")
    def test_passes_checkpointer(self, mock_create):
        mock_create.return_value = MagicMock(spec=CompiledStateGraph)

        model = MagicMock(spec=BaseChatModel)
        checkpointer = MagicMock()

        create_lead_agent(model, [], "prompt", checkpointer=checkpointer)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["checkpointer"] is checkpointer
