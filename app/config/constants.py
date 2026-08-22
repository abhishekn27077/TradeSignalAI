from enum import Enum

from pydantic import BaseModel


# ==========================================
# ENUMERATIONS
# ==========================================
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class PluginType(str, Enum):
    STRATEGY = "strategy"
    AGENT = "agent"
    INDICATOR = "indicator"
    CONNECTOR = "connector"

# ==========================================
# CONSTANTS
# ==========================================
SYSTEM_USER_ID = "system_001"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# ==========================================
# BASE RESPONSE MODELS (DTOs)
# ==========================================
class BaseAPIResponse(BaseModel):
    success: bool
    message: str | None = None

class ErrorResponse(BaseAPIResponse):
    success: bool = False
    error_code: str
    details: dict | None = None
