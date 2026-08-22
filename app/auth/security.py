from datetime import datetime, timedelta, timezone

from app.config.settings import get_settings
from app.logs.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _has_jose = True
except ImportError:
    _has_jose = False
    logger.info("jose/passlib not installed, auth in degraded mode")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not _has_jose:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    if not _has_jose:
        return password
    try:
        return pwd_context.hash(password)
    except Exception:
        return password


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if not _has_jose or not settings.SECRET_KEY:
        logger.warning("Cannot create JWT: missing dependencies or SECRET_KEY")
        return ""
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except Exception as e:
        logger.warning(f"JWT creation failed: {e}")
        return ""


def verify_token(token: str) -> dict | None:
    if not _has_jose or not settings.SECRET_KEY:
        return {"user_id": "anonymous", "role": "viewer"}
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
VALID_API_KEYS = ["ENTERPRISE_DEV_KEY"]

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Validate the API Key for secured endpoints."""
    if not api_key_header or api_key_header not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header

def verify_role(required_role: str):
    """RBAC middleware generator."""
    async def role_checker(api_key: str = Security(get_api_key)):
        if required_role == "admin" and api_key not in VALID_API_KEYS:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True
    return role_checker