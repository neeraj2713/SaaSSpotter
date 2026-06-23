"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.aws.secrets import init_settings_from_secrets
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.mongodb import close_client, ensure_indexes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_settings_from_secrets()
    try:
        ensure_indexes()
    except Exception:
        logger.warning(
            "MongoDB unavailable at startup — read/write endpoints will fail until connected",
            exc_info=True,
        )
    yield
    close_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PainPoint.io API",
        description="Micro-SaaS ideas from real business pain points",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "api"}

    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
