"""Google (Gemini) Provider 适配器。"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from hn_agent.config.models import ModelSettings
from hn_agent.models.credential_loader import load_provider_config


class GoogleProvider:
    """Google 模型提供商适配器。"""

    def create(
        self, model_name: str, config: ModelSettings, **kwargs: Any
    ) -> BaseChatModel:
        provider_cfg = load_provider_config("google", config)

        params: dict[str, Any] = {
            "model": model_name,
            "google_api_key": provider_cfg.api_key,
        }

        if kwargs.get("vision"):
            params.update(provider_cfg.extra.get("vision_params", {}))

        params.update(provider_cfg.extra.get("default_params", {}))

        return ChatGoogleGenerativeAI(**params)
