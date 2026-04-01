"""
模型工厂：根据模型名称前缀路由到对应 Provider 创建 BaseChatModel。

路由规则:
  gpt-     → OpenAI
  claude-  → Anthropic
  deepseek-→ DeepSeek
  gemini-  → Google
  minimax- → MiniMax
  qwen-    → Qwen
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel

from hn_agent.config.models import ModelSettings
from hn_agent.exceptions import UnsupportedProviderError
from hn_agent.models.anthropic_provider import AnthropicProvider
from hn_agent.models.base_provider import ModelProvider
from hn_agent.models.deepseek_provider import DeepSeekProvider
from hn_agent.models.google_provider import GoogleProvider
from hn_agent.models.minimax_provider import MiniMaxProvider
from hn_agent.models.openai_provider import OpenAIProvider
from hn_agent.models.qwen_provider import QwenProvider

# 前缀 → Provider 实例映射
_PREFIX_PROVIDER_MAP: dict[str, ModelProvider] = {
    "gpt-": OpenAIProvider(),
    "o1-": OpenAIProvider(),
    "o3-": OpenAIProvider(),
    "o4-": OpenAIProvider(),
    "claude-": AnthropicProvider(),
    "deepseek-": DeepSeekProvider(),
    "gemini-": GoogleProvider(),
    "minimax-": MiniMaxProvider(),
    "qwen-": QwenProvider(),
}


def _resolve_provider(model_name: str) -> ModelProvider:
    """根据模型名称前缀解析对应的 Provider。"""
    for prefix, provider in _PREFIX_PROVIDER_MAP.items():
        if model_name.startswith(prefix):
            return provider
    raise UnsupportedProviderError(model_name)


def create_model(
    model_name: str,
    *,
    config: ModelSettings | None = None,
    thinking: bool = False,
    vision: bool = False,
    **kwargs: Any,
) -> BaseChatModel:
    """统一模型创建入口，根据模型名称路由到对应 Provider。

    Args:
        model_name: 模型名称（如 "gpt-4o", "claude-3-opus-20240229"）。
        config: 模型工厂配置。若为 None 则使用默认空配置。
        thinking: 是否启用 thinking 模式。
        vision: 是否启用 vision 能力。
        **kwargs: 传递给 Provider 的额外参数。

    Returns:
        LangChain BaseChatModel 实例。

    Raises:
        UnsupportedProviderError: 模型名称不匹配任何已知提供商。
        CredentialError: API 凭证缺失或无效。
    """
    if config is None:
        config = ModelSettings()

    provider = _resolve_provider(model_name)
    return provider.create(
        model_name, config, thinking=thinking, vision=vision, **kwargs
    )
