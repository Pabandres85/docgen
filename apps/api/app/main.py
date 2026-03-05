import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.core.settings import settings
from app.db.session import Base, engine
from app.routes.batches import router as batches_router

logger = logging.getLogger("docgen.api")


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(title="DocGen API", version="0.1.0")

    cors_origins = settings.cors_origins_list
    if settings.environment.lower() == "prod" and "*" in cors_origins:
        raise RuntimeError("CORS_ORIGINS no puede contener '*' en produccion")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)

    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            config=RateLimitConfig(
                max_requests=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window_seconds,
            ),
        )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        return response

    @app.on_event("startup")
    def on_startup():
        if settings.auto_create_tables:
            logger.warning("AUTO_CREATE_TABLES enabled. Creating schema from metadata.")
            Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready():
        checks = {"database": "ok", "redis": "ok"}

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.exception("Database readiness check failed")
            checks["database"] = f"error: {e}"

        try:
            from redis import Redis

            redis_client = Redis.from_url(settings.redis_url, socket_timeout=2)
            if not redis_client.ping():
                checks["redis"] = "error: ping false"
        except Exception as e:
            logger.exception("Redis readiness check failed")
            checks["redis"] = f"error: {e}"

        if all(v == "ok" for v in checks.values()):
            return {"status": "ready", "checks": checks}
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks},
        )

    app.include_router(batches_router)
    return app


app = create_app()
