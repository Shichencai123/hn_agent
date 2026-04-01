"""MiniMax Provider 适配器（OpenAI 兼容）。"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from hn_agent.config.models import ModelSettings
from hn_agent.models.credential_loader import load_provider_config

_DEFAULT_API_BASE = "https://api.minimax.chat/v1"


class MiniMaxProvider:
    """MiniMax 模型提供商适配器（使用 OpenAI 兼容接口）。"""

    def create(
        self, model_name: str, config: ModelSettings, **kwargs: Any
    ) -> BaseChatModel:
        provider_cfg = load_provider_config("minimax", config)

        params: dict[str, Any] = {
            "model": model_name,
            "api_key": provider_cfg.api_key,
            "base_url": provider_cfg.api_base or _DEFAULT_API_BASE,
        }

        params.update(provider_cfg.extra.get("default_params", {}))

        return ChatOpenAI(**params)
