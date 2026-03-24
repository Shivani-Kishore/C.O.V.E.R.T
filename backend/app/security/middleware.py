import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time

from app.security.rate_limiter import rate_limiter, burst_rate_limiter, RateLimitExceeded
from app.security.input_sanitizer import SecurityError

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://ipfs.io https://gateway.pinata.cloud;"
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMIT_EXEMPT_PATHS = ['/health', '/docs', '/redoc', '/openapi.json']

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.RATE_LIMIT_EXEMPT_PATHS:
            return await call_next(request)

        try:
            identifier = rate_limiter.get_identifier(request)

            burst_rate_limiter.check_burst_limit(identifier, max_burst=10, burst_window=10)

            endpoint = request.url.path
            rate_limiter.check_rate_limit(
                identifier,
                max_requests=100,
                window_seconds=60,
                endpoint=endpoint
            )

            response = await call_next(request)
            return response

        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        request_id = request.headers.get('X-Request-ID', 'unknown')

        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[ID: {request_id}]"
        )

        try:
            response = await call_next(request)

            duration = time.time() - start_time

            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[Status: {response.status_code}, Duration: {duration:.2f}s]"
            )

            response.headers['X-Request-ID'] = request_id
            response.headers['X-Response-Time'] = f"{duration:.2f}s"

            return response

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[Error: {str(e)}, Duration: {duration:.2f}s]"
            )
            raise


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    VALIDATION_EXEMPT_PATHS = ['/health', '/docs', '/redoc', '/openapi.json']
    MAX_BODY_SIZE = 10 * 1024 * 1024

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.VALIDATION_EXEMPT_PATHS:
            return await call_next(request)

        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_length = request.headers.get('Content-Length')
                if content_length and int(content_length) > self.MAX_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large"}
                    )

            origin = request.headers.get('Origin')
            if origin:
                from app.core.config import settings
                if origin not in settings.CORS_ORIGINS:
                    logger.warning(f"Request from unauthorized origin: {origin}")

            response = await call_next(request)
            return response

        except SecurityError as e:
            logger.error(f"Security validation failed: {e}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Security validation failed"}
            )
