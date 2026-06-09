from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.config import settings
from app.database import engine

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    log.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION)
    yield
    log.info("shutdown")
    await engine.dispose()


def create_app() -> FastAPI:
    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()], traces_sample_rate=0.1)

    _app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="**Scentara** — Luxury Fragrance E-Commerce API. Manage products, orders, marketplace listings, AI content and automated pricing.",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routers(_app)

    @_app.exception_handler(HTTPException)
    async def http_exc(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "status_code": exc.status_code})

    @_app.exception_handler(ValidationError)
    async def validation_exc(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors(), "status_code": 422})

    @_app.exception_handler(Exception)
    async def unhandled_exc(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_exception", exc=str(exc), path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "status_code": 500})

    @_app.get("/health", tags=["system"])
    async def health() -> dict[str, Any]:
        return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    @_app.get("/metrics", tags=["system"], include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return _app


def _register_routers(_app: FastAPI) -> None:
    prefix = "/api/v1"
    try:
        from app.routers import products, orders, marketplace, admin, import_router, customers, checkout
        _app.include_router(products.router, prefix=prefix)
        _app.include_router(products.brands_router, prefix=prefix)
        _app.include_router(products.categories_router, prefix=prefix)
        _app.include_router(products.collections_router, prefix=prefix)
        _app.include_router(orders.router, prefix=prefix)
        _app.include_router(marketplace.router, prefix=prefix)
        _app.include_router(admin.router, prefix=prefix)
        _app.include_router(import_router.router, prefix=prefix)
        _app.include_router(customers.router, prefix=prefix)
        _app.include_router(customers.auth_router, prefix=prefix)
        _app.include_router(checkout.router, prefix=prefix)
    except ImportError as exc:
        log.warning("router_import_skipped", reason=str(exc))


app = create_app()
