"""Gateway 配置：端口、CORS、API 前缀等。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CORSConfig(BaseModel):
    """CORS 跨域配置。"""

    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True


class GatewayConfig(BaseModel):
    """Gateway 服务配置。"""

    host: str = "0.0.0.0"
    port: int = 8001
    api_prefix: str = "/api"
    debug: bool = False
    cors: CORSConfig = Field(default_factory=CORSConfig)
