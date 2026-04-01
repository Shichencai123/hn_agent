"""配置系统单元测试。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from hn_agent.config.loader import ConfigLoader
from hn_agent.config.models import (
    AppConfig,
    AppSettings,
    ExtensionsSettings,
    GuardrailSettings,
    MemorySettings,
    ModelSettings,
    ProviderConfig,
    SandboxSettings,
    ToolSettings,
    VectorStoreSettings,
)
from hn_agent.exceptions import ConfigurationError


# ── 模型默认值 ──────────────────────────────────────────


class TestConfigModels:
    """配置模型默认值和类型验证。"""

    def test_app_config_all_defaults(self):
        cfg = AppConfig()
        assert cfg.version == "1.0"
        assert isinstance(cfg.app, AppSettings)
        assert isinstance(cfg.model, ModelSettings)
        assert isinstance(cfg.sandbox, SandboxSettings)
        assert isinstance(cfg.tool, ToolSettings)
        assert isinstance(cfg.memory, MemorySettings)
        assert isinstance(cfg.extensions, ExtensionsSettings)
        assert isinstance(cfg.guardrails, GuardrailSettings)

    def test_app_settings_defaults(self):
        s = AppSettings()
        assert s.name == "hn-agent"
        assert s.debug is False
        assert s.port == 8001

    def test_model_settings_defaults(self):
        s = ModelSettings()
        assert s.default_model == "gpt-4o"
        assert s.providers == {}

    def test_provider_config(self):
        p = ProviderConfig(api_key="sk-test", api_base="https://api.example.com")
        assert p.api_key == "sk-test"
        assert p.api_base == "https://api.example.com"
        assert p.extra == {}

    def test_sandbox_settings_defaults(self):
        s = SandboxSettings()
        assert s.provider == "local"
        assert s.timeout == 30
        assert s.work_dir == "./data/sandbox"

    def test_memory_settings_defaults(self):
        s = MemorySettings()
        assert s.enabled is True
        assert s.debounce_seconds == 5.0
        assert isinstance(s.vector_store, VectorStoreSettings)

    def test_vector_store_settings_defaults(self):
        s = VectorStoreSettings()
        assert s.provider == "chromadb"
        assert s.top_k == 5
        assert s.embedding_model == "text-embedding-3-small"

    def test_guardrail_settings_defaults(self):
        s = GuardrailSettings()
        assert s.enabled is True
        assert s.provider == "builtin"

    def test_app_config_custom_values(self):
        cfg = AppConfig(
            app=AppSettings(name="my-agent", debug=True, port=9000),
            model=ModelSettings(
                default_model="claude-3",
                providers={"anthropic": ProviderConfig(api_key="key")},
            ),
            version="2.0",
        )
        assert cfg.app.name == "my-agent"
        assert cfg.app.debug is True
        assert cfg.model.default_model == "claude-3"
        assert cfg.model.providers["anthropic"].api_key == "key"
        assert cfg.version == "2.0"


# ── YAML 加载 ──────────────────────────────────────────


class TestConfigLoaderYAML:
    """YAML 配置文件加载。"""

    def test_load_yaml(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            yaml.dump(
                {
                    "app": {"name": "test-agent", "port": 9000},
                    "version": "2.0",
                }
            )
        )
        loader = ConfigLoader()
        cfg = loader.load(str(cfg_file))
        assert cfg.app.name == "test-agent"
        assert cfg.app.port == 9000
        assert cfg.version == "2.0"

    def test_load_yml_extension(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yml"
        cfg_file.write_text(yaml.dump({"app": {"debug": True}}))
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.app.debug is True

    def test_load_minimal_yaml(self, tmp_path: Path):
        """空字典应使用全部默认值。"""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({}))
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.version == "1.0"
        assert cfg.app.name == "hn-agent"


# ── JSON 加载 ──────────────────────────────────────────


class TestConfigLoaderJSON:
    """JSON 配置文件加载。"""

    def test_load_json(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "app": {"name": "json-agent"},
                    "sandbox": {"timeout": 60},
                }
            )
        )
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.app.name == "json-agent"
        assert cfg.sandbox.timeout == 60


# ── 环境变量覆盖 ──────────────────────────────────────────


class TestEnvOverrides:
    """环境变量覆盖配置项。"""

    def test_env_override_simple(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"app": {"name": "original"}}))

        monkeypatch.setenv("HN_AGENT_APP__NAME", "overridden")
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.app.name == "overridden"

    def test_env_override_nested(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"sandbox": {"provider": "local"}}))

        monkeypatch.setenv("HN_AGENT_SANDBOX__PROVIDER", "docker")
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.sandbox.provider == "docker"

    def test_env_override_top_level(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"version": "1.0"}))

        monkeypatch.setenv("HN_AGENT_VERSION", "3.0")
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.version == "3.0"

    def test_env_override_creates_missing_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({}))

        monkeypatch.setenv("HN_AGENT_APP__PORT", "7777")
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.app.port == 7777


# ── 未知配置项 ──────────────────────────────────────────


class TestUnknownKeys:
    """未知配置项应被忽略。"""

    def test_unknown_top_level_key_ignored(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            yaml.dump({"app": {"name": "test"}, "unknown_section": {"foo": "bar"}})
        )
        cfg = ConfigLoader().load(str(cfg_file))
        assert cfg.app.name == "test"
        assert not hasattr(cfg, "unknown_section")

    def test_load_from_dict_ignores_unknown(self):
        cfg = ConfigLoader().load_from_dict(
            {"version": "1.0", "totally_unknown": 42, "another": "nope"}
        )
        assert cfg.version == "1.0"


# ── 错误处理 ──────────────────────────────────────────


class TestErrorHandling:
    """错误场景。"""

    def test_file_not_found(self):
        with pytest.raises(ConfigurationError, match="配置文件不存在"):
            ConfigLoader().load("/nonexistent/path/config.yaml")

    def test_unsupported_format(self, tmp_path: Path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[app]\nname = 'test'")
        with pytest.raises(ConfigurationError, match="不支持的配置文件格式"):
            ConfigLoader().load(str(cfg_file))

    def test_non_dict_content(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("- item1\n- item2\n")
        with pytest.raises(ConfigurationError, match="字典格式"):
            ConfigLoader().load(str(cfg_file))

    def test_required_field_missing_raises_configuration_error(self):
        """ModelSettings.default_model 是必需字段（无默认值时）。
        但当前所有字段都有默认值，所以我们通过传入非法类型触发验证错误。
        """
        # 传入非法类型给 sandbox.timeout（期望 int）
        with pytest.raises(ConfigurationError):
            ConfigLoader().load_from_dict({"sandbox": {"timeout": "not_a_number"}})


# ── load_from_dict ──────────────────────────────────────


class TestLoadFromDict:
    """从字典加载配置。"""

    def test_basic(self):
        cfg = ConfigLoader().load_from_dict({"app": {"name": "dict-agent"}})
        assert cfg.app.name == "dict-agent"

    def test_full_config(self):
        data = {
            "app": {"name": "full", "debug": True, "port": 3000},
            "model": {
                "default_model": "claude-3",
                "providers": {
                    "anthropic": {"api_key": "sk-ant", "api_base": "https://api.anthropic.com"},
                },
            },
            "sandbox": {"provider": "docker", "timeout": 120},
            "memory": {
                "enabled": False,
                "vector_store": {"provider": "pinecone", "top_k": 10},
            },
            "version": "2.5",
        }
        cfg = ConfigLoader().load_from_dict(data)
        assert cfg.app.name == "full"
        assert cfg.model.providers["anthropic"].api_key == "sk-ant"
        assert cfg.sandbox.provider == "docker"
        assert cfg.memory.enabled is False
        assert cfg.memory.vector_store.provider == "pinecone"
        assert cfg.version == "2.5"
