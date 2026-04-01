"""
配置数据模型：基于 Pydantic BaseModel 的类型化配置。

所有配置模型均使用 Pydantic v2 语法，提供类型验证和 JSON Schema 生成。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    """应用基础设置。"""

    name: str = "hn-agent"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8001


class ProviderConfig(BaseModel):
    """单个 LLM 提供商配置。"""

    api_key: str | None = None
    api_base: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ModelSettings(BaseModel):
    """模型工厂配置。"""

    default_model: str = "gpt-4o"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class SandboxSettings(BaseModel):
    """沙箱系统配置。"""

    provider: str = "local"
    timeout: int = 30
    work_dir: str = "./data/sandbox"


class ToolSettings(BaseModel):
    """工具系统配置。"""

    builtin_enabled: bool = True
    community_tools: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)


class VectorStoreSettings(BaseModel):
    """向量存储配置。"""

    provider: str = "chromadb"
    collection_name: str = "hn_agent_memories"
    embedding_model: str = "text-embedding-3-small"
    persist_directory: str = "./data/chromadb"
    top_k: int = 5


class MemorySettings(BaseModel):
    """记忆系统配置。"""

    enabled: bool = True
    debounce_seconds: float = 5.0
    storage_dir: str = "./data/memory"
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)


class ExtensionsSettings(BaseModel):
    """扩展配置。"""

    enabled: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class GuardrailSettings(BaseModel):
    """护栏系统配置。"""

    enabled: bool = True
    provider: str = "builtin"
    rules: list[dict[str, Any]] = Field(default_factory=list)


class AppConfig(BaseModel):
    """应用顶层配置，聚合所有子模块配置。"""

    app: AppSettings = Field(default_factory=AppSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    tool: ToolSettings = Field(default_factory=ToolSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    extensions: ExtensionsSettings = Field(default_factory=ExtensionsSettings)
    guardrails: GuardrailSettings = Field(default_factory=GuardrailSettings)
    version: str = "1.0"
