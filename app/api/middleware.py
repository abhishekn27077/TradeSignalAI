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

class CanonicalFingerprintMiddleware(BaseHTTPMiddleware):
    """
    Phase 60: Appends canonical response fingerprint headers to every API response:
    - X-Canonical-Engine-Version
    - X-Git-Commit
    - X-Config-Hash
    - X-Canonical-State-ID
    - X-Generated-At
    - X-Market-Data-Timestamp
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        try:
            from app.core.canonical_signal_service import canonical_signal_service, CONFIG_HASH
            snapshot = canonical_signal_service.get_active_snapshot()
            meta = snapshot.runtime_metadata
            response.headers["X-Canonical-Engine-Version"] = str(meta.get("runtime_phase", "PHASE 60"))
            response.headers["X-Git-Commit"] = str(meta.get("git_commit", "ddcba51"))
            response.headers["X-Config-Hash"] = str(CONFIG_HASH)
            response.headers["X-Canonical-State-ID"] = str(snapshot.snapshot_id)
            response.headers["X-Snapshot-Content-Hash"] = str(snapshot.snapshot_content_hash)
            response.headers["X-Generated-At"] = str(snapshot.created_at)
            response.headers["X-Market-Data-Timestamp"] = str(snapshot.market_data_timestamp)
        except Exception:
            pass
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

class StateChangingAuthMiddleware(BaseHTTPMiddleware):
    """
    Phase 74: Enforces strict authentication for state-changing HTTP methods
    (POST, PUT, PATCH, DELETE) across all control, execution, and admin endpoints.
    Fails closed with 401 Unauthorized if credentials are missing or invalid.
    """
    EXEMPT_PATHS = {
        "/api/v1/auth/token",
        "/api/v1/auth/login",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/",
    }

    READ_ONLY_POST_PATHS = {
        "/api/v1/system-intelligence/ensemble/evaluate",
        "/api/v1/system-intelligence/signal-quality/evaluate",
        "/api/v1/system-intelligence/execution/simulate",
        "/api/v1/system-intelligence/pipeline/run",
        "/api/v1/signals/point-in-time-replay",
        "/api/v1/signals/replay",
        "/api/v1/research/sweep",
        "/api/v1/validation/phase44/replay",
        "/api/v1/signals/auto-resolve",
        "/api/v1/signals/run-cycle",
        "/api/v1/signals/resolve-due",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            path = request.url.path
            is_exempt = (
                path in self.EXEMPT_PATHS
                or path in self.READ_ONLY_POST_PATHS
                or path.endswith("/revalidate")
            )
            if not is_exempt:
                auth_header = request.headers.get("Authorization")
                api_key_header = request.headers.get("X-API-Key")

                authenticated = False
                user = None

                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1].strip()
                    try:
                        from app.auth.security import verify_token
                        user = verify_token(token)
                        if user and user.get("user_id") != "anonymous":
                            authenticated = True
                    except Exception:
                        authenticated = False

                if not authenticated and api_key_header:
                    from app.config.settings import get_settings
                    settings = get_settings()
                    if api_key_header in settings.VALID_API_KEYS:
                        authenticated = True

                if not authenticated:
                    return JSONResponse(
                        status_code=401,
                        content=structured_error_response(
                            message="Authentication required for state-changing endpoint",
                            error_code="UNAUTHORIZED",
                            recoverable=False,
                            retrying=False,
                            status="unauthorized",
                        ),
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                if user:
                    request.state.user = user

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in ["127.0.0.1", "localhost", "::1", "testclient"]:
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
    from app.logs.logger import redact_sensitive_text

    correlation_id = getattr(request.state, "correlation_id", "unknown")

    if isinstance(exc, BaseAPIException):
        sanitized_details = {
            "provider": exc.provider,
            "recoverable": exc.recoverable,
            "timestamp": exc.timestamp,
        }
        if exc.details:
            for k, v in exc.details.items():
                sanitized_details[k] = redact_sensitive_text(str(v)) if isinstance(v, str) else v

        content = ErrorResponse(
            success=False,
            message=redact_sensitive_text(exc.message),
            error_code=exc.error_code,
            details=sanitized_details,
        ).model_dump()
        status_code = exc.status_code
        logger.warning(
            f"API Exception: {exc.error_code} - {content['message']}",
            extra={"correlation_id": correlation_id},
        )
    elif isinstance(exc, ValueError):
        content = ErrorResponse(
            success=False,
            message=redact_sensitive_text(str(exc)),
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