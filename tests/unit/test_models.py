"""模型工厂单元测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models import BaseChatModel

from hn_agent.config.models import ModelSettings, ProviderConfig
from hn_agent.exceptions import CredentialError, UnsupportedProviderError
from hn_agent.models.credential_loader import load_provider_config
from hn_agent.models.factory import _resolve_provider, create_model


# ── Helpers ──────────────────────────────────────────────


def _make_config(**provider_entries: dict) -> ModelSettings:
    """快速构建 ModelSettings，provider_entries 格式: provider_name={"api_key": ...}"""
    providers = {
        name: ProviderConfig(**cfg) for name, cfg in provider_entries.items()
    }
    return ModelSettings(providers=providers)


# ── credential_loader 测试 ───────────────────────────────


class TestCredentialLoader:
    def test_load_existing_provider(self):
        config = _make_config(openai={"api_key": "sk-test"})
        result = load_provider_config("openai", config)
        assert result.api_key == "sk-test"

    def test_missing_provider_raises(self):
        config = _make_config()
        with pytest.raises(CredentialError, match="openai"):
            load_provider_config("openai", config)

    def test_empty_api_key_raises(self):
        config = _make_config(openai={"api_key": ""})
        with pytest.raises(CredentialError, match="API Key 缺失"):
            load_provider_config("openai", config)

    def test_none_api_key_raises(self):
        config = _make_config(openai={})
        with pytest.raises(CredentialError, match="API Key 缺失"):
            load_provider_config("openai", config)


# ── _resolve_provider 测试 ───────────────────────────────


class TestResolveProvider:
    @pytest.mark.parametrize(
        "model_name,expected_cls",
        [
            ("gpt-4o", "OpenAIProvider"),
            ("gpt-3.5-turbo", "OpenAIProvider"),
            ("o1-preview", "OpenAIProvider"),
            ("o3-mini", "OpenAIProvider"),
            ("o4-mini", "OpenAIProvider"),
            ("claude-3-opus-20240229", "AnthropicProvider"),
            ("claude-3-5-sonnet-20241022", "AnthropicProvider"),
            ("deepseek-chat", "DeepSeekProvider"),
            ("deepseek-coder", "DeepSeekProvider"),
            ("gemini-1.5-pro", "GoogleProvider"),
            ("gemini-2.0-flash", "GoogleProvider"),
            ("minimax-abab6.5", "MiniMaxProvider"),
            ("qwen-turbo", "QwenProvider"),
            ("qwen-max", "QwenProvider"),
        ],
    )
    def test_prefix_routing(self, model_name: str, expected_cls: str):
        provider = _resolve_provider(model_name)
        assert type(provider).__name__ == expected_cls

    def test_unknown_prefix_raises(self):
        with pytest.raises(UnsupportedProviderError, match="unknown-model"):
            _resolve_provider("unknown-model")


# ── create_model 集成测试（mock LLM 构造） ──────────────


class TestCreateModel:
    def test_unsupported_provider(self):
        with pytest.raises(UnsupportedProviderError):
            create_model("llama-3-70b")

    def test_missing_credentials(self):
        config = _make_config()
        with pytest.raises(CredentialError):
            create_model("gpt-4o", config=config)

    @patch("hn_agent.models.openai_provider.ChatOpenAI")
    def test_openai_creates_model(self, mock_cls: MagicMock):
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_cls.return_value = mock_instance

        config = _make_config(openai={"api_key": "sk-test"})
        result = create_model("gpt-4o", config=config)

        assert result is mock_instance
        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["api_key"] == "sk-test"

    @patch("hn_agent.models.openai_provider.ChatOpenAI")
    def test_openai_with_custom_base(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(
            openai={"api_key": "sk-test", "api_base": "https://custom.api/v1"}
        )
        create_model("gpt-4o", config=config)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["base_url"] == "https://custom.api/v1"

    @patch("hn_agent.models.anthropic_provider.ChatAnthropic")
    def test_anthropic_creates_model(self, mock_cls: MagicMock):
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_cls.return_value = mock_instance

        config = _make_config(anthropic={"api_key": "sk-ant-test"})
        result = create_model("claude-3-opus-20240229", config=config)

        assert result is mock_instance
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "claude-3-opus-20240229"
        assert call_kwargs["api_key"] == "sk-ant-test"

    @patch("hn_agent.models.anthropic_provider.ChatAnthropic")
    def test_anthropic_thinking_mode(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(anthropic={"api_key": "sk-ant-test"})
        create_model("claude-3-opus-20240229", config=config, thinking=True)

        call_kwargs = mock_cls.call_args[1]
        assert "thinking" in call_kwargs
        assert call_kwargs["thinking"]["type"] == "enabled"

    @patch("hn_agent.models.deepseek_provider.ChatOpenAI")
    def test_deepseek_uses_openai_compat(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(deepseek={"api_key": "sk-ds-test"})
        create_model("deepseek-chat", config=config)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "deepseek-chat"
        assert "deepseek" in call_kwargs["base_url"]

    @patch("hn_agent.models.google_provider.ChatGoogleGenerativeAI")
    def test_google_creates_model(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(google={"api_key": "google-key"})
        create_model("gemini-1.5-pro", config=config)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "gemini-1.5-pro"
        assert call_kwargs["google_api_key"] == "google-key"

    @patch("hn_agent.models.minimax_provider.ChatOpenAI")
    def test_minimax_uses_openai_compat(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(minimax={"api_key": "mm-key"})
        create_model("minimax-abab6.5", config=config)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "minimax-abab6.5"
        assert "minimax" in call_kwargs["base_url"]

    @patch("hn_agent.models.qwen_provider.ChatOpenAI")
    def test_qwen_uses_openai_compat(self, mock_cls: MagicMock):
        mock_cls.return_value = MagicMock(spec=BaseChatModel)

        config = _make_config(qwen={"api_key": "qwen-key"})
        create_model("qwen-turbo", config=config)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "qwen-turbo"
        assert "dashscope" in call_kwargs["base_url"]

    @patch("hn_agent.models.openai_provider.ChatOpenAI")
    def test_default_config_when_none(self, mock_cls: MagicMock):
        """config=None 时使用默认 ModelSettings，应因缺少凭证而报错。"""
        with pytest.raises(CredentialError):
            create_model("gpt-4o")
