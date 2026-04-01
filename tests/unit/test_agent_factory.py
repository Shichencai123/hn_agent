"""Agent 工厂与特性管理单元测试。"""

from __future__ import annotations

import pytest

from hn_agent.agents.features import Features
from hn_agent.agents.factory import AgentConfig


# ── Features 测试 ────────────────────────────────────────


class TestFeatures:
    def test_default_all_enabled(self):
        f = Features()
        assert f.sandbox_enabled is True
        assert f.memory_enabled is True
        assert f.subagent_enabled is True
        assert f.guardrail_enabled is True
        assert f.mcp_enabled is True

    def test_from_config_partial(self):
        f = Features.from_config({"sandbox_enabled": False, "mcp_enabled": False})
        assert f.sandbox_enabled is False
        assert f.mcp_enabled is False
        # 未指定的保持默认
        assert f.memory_enabled is True
        assert f.subagent_enabled is True
        assert f.guardrail_enabled is True

    def test_from_config_all_disabled(self):
        f = Features.from_config({
            "sandbox_enabled": False,
            "memory_enabled": False,
            "subagent_enabled": False,
            "guardrail_enabled": False,
            "mcp_enabled": False,
        })
        assert f.sandbox_enabled is False
        assert f.memory_enabled is False
        assert f.subagent_enabled is False
        assert f.guardrail_enabled is False
        assert f.mcp_enabled is False

    def test_from_config_ignores_unknown_keys(self):
        f = Features.from_config({
            "sandbox_enabled": True,
            "unknown_feature": True,
            "another_thing": False,
        })
        assert f.sandbox_enabled is True
        assert not hasattr(f, "unknown_feature")

    def test_from_config_empty_dict(self):
        f = Features.from_config({})
        # 全部使用默认值
        assert f.sandbox_enabled is True
        assert f.memory_enabled is True

    def test_from_config_truthy_values(self):
        f = Features.from_config({"sandbox_enabled": 1, "memory_enabled": 0})
        assert f.sandbox_enabled is True
        assert f.memory_enabled is False


# ── AgentConfig 测试 ─────────────────────────────────────


class TestAgentConfig:
    def test_default_values(self):
        config = AgentConfig()
        assert config.agent_id == "default"
        assert config.name == "Lead Agent"
        assert config.model_name == "gpt-4o"
        assert isinstance(config.features, Features)
        assert config.skill_names == []
        assert config.mcp_servers == []
        assert config.community_tools == []
        assert config.custom_settings == {}

    def test_custom_values(self):
        features = Features(sandbox_enabled=False)
        config = AgentConfig(
            agent_id="custom-1",
            name="Custom Agent",
            model_name="claude-3-opus",
            features=features,
            skill_names=["search", "code"],
            mcp_servers=["server-1"],
            community_tools=["tavily"],
            custom_settings={"key": "value"},
        )
        assert config.agent_id == "custom-1"
        assert config.name == "Custom Agent"
        assert config.model_name == "claude-3-opus"
        assert config.features.sandbox_enabled is False
        assert config.skill_names == ["search", "code"]
        assert config.mcp_servers == ["server-1"]
        assert config.community_tools == ["tavily"]
        assert config.custom_settings == {"key": "value"}

    def test_independent_list_instances(self):
        """确保不同 AgentConfig 实例的列表字段互不影响。"""
        c1 = AgentConfig()
        c2 = AgentConfig()
        c1.skill_names.append("test")
        assert c2.skill_names == []
