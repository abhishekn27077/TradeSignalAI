import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import (
    BaseAPIException,
    structured_error_response,
)
from app.config.constants import ErrorResponse
from app.logs.logger import get_logger

logger = get_logger(__name__)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            return await call_next(request)

        now = time.time()
        self._requests = {
            ip: timestamps for ip, timestamps in self._requests.items()
            if timestamps and timestamps[-1] > now - self.window_seconds
        }
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        timestamps = self._requests[client_ip]
        timestamps.insert(0, now)
        if len(timestamps) > self.max_requests:
            return JSONResponse(
                status_code=429,
                content=structured_error_response(
                    message="Rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED",
                    recoverable=True,
                    retrying=True,
                    status="rate_limited",
                ),
            )
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger.info(
            f"Request Started: {request.method} {request.url.path}",
            extra={"correlation_id": correlation_id},
        )
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"Request Completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.4f}s",
                extra={"correlation_id": correlation_id},
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request Failed: {request.method} {request.url.path} - Duration: {process_time:.4f}s",
                exc_info=True,
                extra={"correlation_id": correlation_id},
            )
            raise e

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    if isinstance(exc, BaseAPIException):
        content = ErrorResponse(
            success=False,
            message=exc.message,
            error_code=exc.error_code,
            details={
                "provider": exc.provider,
                "recoverable": exc.recoverable,
                "timestamp": exc.timestamp,
                **(exc.details or {}),
            },
        ).model_dump()
        status_code = exc.status_code
        logger.warning(
            f"API Exception: {exc.error_code} - {exc.message}",
            extra={"correlation_id": correlation_id},
        )
    elif isinstance(exc, ValueError):
        content = ErrorResponse(
            success=False,
            message=str(exc),
            error_code="VALIDATION_ERROR",
            details={"recoverable": False},
        ).model_dump()
        status_code = 422
    elif isinstance(exc, ConnectionError):
        content = ErrorResponse(
            success=False,
            message="A connection error occurred. The service will retry automatically.",
            error_code="CONNECTION_ERROR",
            details={"recoverable": True, "retrying": True},
        ).model_dump()
        status_code = 503
    elif isinstance(exc, TimeoutError):
        content = ErrorResponse(
            success=False,
            message="The request timed out.",
            error_code="TIMEOUT_ERROR",
            details={"recoverable": True, "retrying": True},
        ).model_dump()
        status_code = 504
    else:
        content = ErrorResponse(
            success=False,
            message="An unexpected error occurred. The system has been notified.",
            error_code="INTERNAL_SERVER_ERROR",
            details={"recoverable": True},
        ).model_dump()
        status_code = 500
        logger.error(
            "Unhandled Exception",
            exc_info=exc,
            extra={"correlation_id": correlation_id},
        )

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"X-Correlation-ID": correlation_id},
    )