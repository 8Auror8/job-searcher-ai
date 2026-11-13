"""HTTP middlewares: request id + access log, CSRF (double submit cookie), security headers."""

import secrets
import time
import uuid

import structlog
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.errors import CsrfFailed, error_body

log = structlog.get_logger()

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
        )
        return response


class CsrfMiddleware(BaseHTTPMiddleware):
    """Unsafe requests that carry session cookies must echo the CSRF cookie in a header."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in SAFE_METHODS:
            has_session = ACCESS_COOKIE in request.cookies or REFRESH_COOKIE in request.cookies
            if has_session:
                cookie = request.cookies.get(CSRF_COOKIE, "")
                header = request.headers.get(CSRF_HEADER, "")
                if not cookie or not secrets.compare_digest(cookie, header):
                    err = CsrfFailed()
                    return JSONResponse(error_body(err.code, err.message), status_code=403)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, production: bool) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.production = production

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        h = response.headers
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "strict-origin-when-cross-origin"
        h["X-Frame-Options"] = "DENY"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if self.production:
            h["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            h["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/auth") or request.url.path.startswith("/api/users"):
            h["Cache-Control"] = "no-store"
        return response
