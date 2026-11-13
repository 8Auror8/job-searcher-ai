"""Application factory."""

from fastapi import FastAPI

from app.api.routes import auth, cvs, health, users
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import CsrfMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import limiter


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(json=settings.is_production)

    app = FastAPI(
        title="JobPilot AI API",
        version="0.1.0",
        docs_url=None if settings.is_production else "/api/docs",
        openapi_url=None if settings.is_production else "/api/openapi.json",
        redoc_url=None,
    )
    app.state.limiter = limiter

    # Starlette runs the last-added middleware first.
    app.add_middleware(SecurityHeadersMiddleware, production=settings.is_production)
    app.add_middleware(CsrfMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    for router in (health.router, auth.router, users.router, cvs.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
