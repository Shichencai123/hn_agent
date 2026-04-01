"""Anthropic (Claude) Provider 适配器。"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from hn_agent.config.models import ModelSettings
from hn_agent.models.credential_loader import load_provider_config


class AnthropicProvider:
    """Anthropic 模型提供商适配器。"""

    def create(
        self, model_name: str, config: ModelSettings, **kwargs: Any
    ) -> BaseChatModel:
        provider_cfg = load_provider_config("anthropic", config)

        params: dict[str, Any] = {
            "model": model_name,
            "api_key": provider_cfg.api_key,
        }

        if provider_cfg.api_base:
            params["base_url"] = provider_cfg.api_base

        if kwargs.get("thinking"):
            params["thinking"] = {"type": "enabled", "budget_tokens": 10000}

        params.update(provider_cfg.extra.get("default_params", {}))

        return ChatAnthropic(**params)
