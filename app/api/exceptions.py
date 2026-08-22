import datetime
from typing import Any


class BaseAPIException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
        recoverable: bool = True,
        provider: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.recoverable = recoverable
        self.provider = provider
        self.timestamp = datetime.datetime.utcnow().isoformat()
        super().__init__(self.message)

class ResourceNotFoundException(BaseAPIException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found.",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
        )

class ValidationException(BaseAPIException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )

class AuthenticationException(BaseAPIException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )

class AuthorizationException(BaseAPIException):
    def __init__(self, message: str = "Permission denied."):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )

class DatabaseException(BaseAPIException):
    def __init__(self, message: str = "A database error occurred.", recoverable: bool = True):
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATABASE_ERROR",
            recoverable=recoverable,
            provider="database",
        )

class ProviderException(BaseAPIException):
    def __init__(
        self,
        provider: str,
        message: str = "Provider unavailable.",
        status_code: int = 503,
        error_code: str = "PROVIDER_ERROR",
        recoverable: bool = True,
        retrying: bool = True,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            recoverable=recoverable,
            provider=provider,
            details={"retrying": retrying, "provider": provider},
        )

class BrokerException(ProviderException):
    def __init__(self, provider: str = "broker", message: str = "Broker unavailable.", recoverable: bool = True):
        super().__init__(provider=provider, message=message, error_code="BROKER_ERROR", recoverable=recoverable)

class MarketDataException(ProviderException):
    def __init__(self, provider: str = "market_data", message: str = "Market data unavailable.", recoverable: bool = True):
        super().__init__(provider=provider, message=message, error_code="MARKET_DATA_ERROR", recoverable=recoverable)

class AIProviderException(ProviderException):
    def __init__(self, provider: str = "ai", message: str = "AI provider unavailable.", recoverable: bool = True):
        super().__init__(provider=provider, message=message, error_code="AI_PROVIDER_ERROR", recoverable=recoverable)

class ExecutionException(BaseAPIException):
    def __init__(self, message: str, details: dict[str, Any] | None = None, recoverable: bool = True):
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXECUTION_ERROR",
            details=details,
            recoverable=recoverable,
            provider="execution",
        )

class ConfigurationException(BaseAPIException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            recoverable=False,
        )

def structured_error_response(
    success: bool = False,
    provider: str | None = None,
    status: str = "error",
    message: str = "An error occurred.",
    retrying: bool = True,
    error_code: str = "INTERNAL_ERROR",
    recoverable: bool = True,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": success,
        "provider": provider,
        "status": status,
        "message": message,
        "retrying": retrying,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "error_code": error_code,
        "recoverable": recoverable,
        **(details or {}),
    }

def provider_offline_response(provider_name: str, message: str | None = None) -> dict[str, Any]:
    return structured_error_response(
        provider=provider_name,
        status="offline",
        message=message or f"{provider_name} is offline.",
        error_code=f"{provider_name.upper()}_OFFLINE",
        recoverable=True,
        retrying=True,
    )

def safe_execute(fn, default_return=None, logger=None, provider_name: str = "unknown"):
    try:
        return fn()
    except Exception as e:
        if logger:
            logger.warning(f"{provider_name} call failed: {e}", exc_info=False)
        return default_return