"""
模型提供商抽象接口。

所有 LLM Provider 适配器均实现 ModelProvider Protocol。
"""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from hn_agent.config.models import ModelSettings


class ModelProvider(Protocol):
    """LLM 提供商的统一协议接口。"""

    def create(
        self, model_name: str, config: ModelSettings, **kwargs: Any
    ) -> BaseChatModel:
        """创建 LLM 模型实例。

        Args:
            model_name: 模型名称（如 "gpt-4o", "claude-3-opus"）。
            config: 模型工厂配置，包含 providers 字典。
            **kwargs: 额外参数（如 thinking, vision）。

        Returns:
            LangChain BaseChatModel 实例。
        """
        ...
