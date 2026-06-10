"""Security middleware: HTTP security headers + structured audit logging.

SecurityHeadersMiddleware adds defensive headers to every response.
AuditLogMiddleware logs every state-changing request (POST/PUT/PATCH/DELETE)
with user identity, IP, path, status code, and duration.
"""
from __future__ import annotations
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

audit_log = structlog.get_logger("audit")


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

_COMMON_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
        "frame-src https://js.stripe.com; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' https://api.stripe.com"
    ),
}

_HSTS = "max-age=31536000; includeSubDomains; preload"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in _COMMON_HEADERS.items():
            response.headers[name] = value
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = _HSTS
        return response


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

_AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Structured audit log for all state-changing requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _AUDIT_METHODS or request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        user_id = _extract_user_id(request)
        client_ip = _get_client_ip(request)

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        audit_log.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            user_id=user_id,
            ip=client_ip,
            duration_ms=duration_ms,
            query=str(request.url.query) or None,
        )
        return response


def _extract_user_id(request: Request) -> str | None:
    """Pull the JWT subject without doing a full DB lookup (best-effort)."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:]
    try:
        from app.core.auth import decode_token
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        return None


def _get_client_ip(request: Request) -> str:
    """Return real IP honouring X-Forwarded-For (set by reverse proxy)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
