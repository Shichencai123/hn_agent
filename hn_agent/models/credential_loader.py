"""
凭证加载器：从 Config_System 加载 API 凭证。
"""

from __future__ import annotations

from hn_agent.config.models import ModelSettings, ProviderConfig
from hn_agent.exceptions import CredentialError


def load_provider_config(
    provider_name: str, config: ModelSettings
) -> ProviderConfig:
    """从 ModelSettings 中加载指定提供商的配置。

    Args:
        provider_name: 提供商名称（如 "openai", "anthropic"）。
        config: 模型工厂配置。

    Returns:
        对应提供商的 ProviderConfig。

    Raises:
        CredentialError: 提供商配置不存在或 API Key 缺失。
    """
    provider_cfg = config.providers.get(provider_name)
    if provider_cfg is None:
        raise CredentialError(provider_name, detail="未配置该提供商")

    if not provider_cfg.api_key:
        raise CredentialError(provider_name, detail="API Key 缺失")

    return provider_cfg
