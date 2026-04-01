"""FastAPI 应用入口：创建应用实例、配置 CORS、注册路由。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.gateway.config import GatewayConfig


def create_app(config: GatewayConfig | None = None) -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    Args:
        config: Gateway 配置，为 None 时使用默认配置。

    Returns:
        配置完成的 FastAPI 实例。
    """
    config = config or GatewayConfig()

    app = FastAPI(
        title="HN Agent Gateway",
        description="HN Agent REST API Gateway",
        version="0.1.0",
        debug=config.debug,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )

    # 注册路由
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """注册所有 API 路由模块。"""
    from app.gateway.routers.agents import router as agents_router
    from app.gateway.routers.artifacts import router as artifacts_router
    from app.gateway.routers.channels import router as channels_router
    from app.gateway.routers.mcp import router as mcp_router
    from app.gateway.routers.memory import router as memory_router
    from app.gateway.routers.models import router as models_router
    from app.gateway.routers.skills import router as skills_router
    from app.gateway.routers.suggestions import router as suggestions_router
    from app.gateway.routers.threads import router as threads_router
    from app.gateway.routers.uploads import router as uploads_router

    app.include_router(models_router)
    app.include_router(mcp_router)
    app.include_router(skills_router)
    app.include_router(memory_router)
    app.include_router(uploads_router)
    app.include_router(threads_router)
    app.include_router(artifacts_router)
    app.include_router(suggestions_router)
    app.include_router(agents_router)
    app.include_router(channels_router)
