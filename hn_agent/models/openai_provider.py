"""OpenAI Provider 适配器。"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from hn_agent.config.models import ModelSettings
from hn_agent.models.credential_loader import load_provider_config


class OpenAIProvider:
    """OpenAI 模型提供商适配器。"""

    def create(
        self, model_name: str, config: ModelSettings, **kwargs: Any
    ) -> BaseChatModel:
        provider_cfg = load_provider_config("openai", config)

        params: dict[str, Any] = {
            "model": model_name,
            "api_key": provider_cfg.api_key,
        }

        if provider_cfg.api_base:
            params["base_url"] = provider_cfg.api_base

        if kwargs.get("thinking"):
            params.update(provider_cfg.extra.get("thinking_params", {}))

        params.update(provider_cfg.extra.get("default_params", {}))

        return ChatOpenAI(**params)
