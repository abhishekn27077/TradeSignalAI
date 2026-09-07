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
    logger.critical(
        "CRITICAL: Required libraries 'python-jose[cryptography]' or 'passlib[bcrypt]' are not installed. "
        "Authentication is disabled. Installation required for secure password hashing."
    )
    # We fail closed — all auth paths will raise HTTPException due to missing SECRET_KEY
    # and this import failure will crash the app during startup, which is the safest outcome.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash. Fails closed if dependencies unavailable."""
    if not _has_jose:
        raise RuntimeError(
            "Cannot verify password: authentication libraries not available. "
            "Install 'python-jose[cryptography]' and 'passlib[bcrypt]' before starting."
        )
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. Fails closed if dependencies unavailable."""
    if not _has_jose:
        raise RuntimeError(
            "Cannot hash password: authentication libraries not available. "
            "Install 'python-jose[cryptography]' and 'passlib[bcrypt]' before starting."
        )
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise RuntimeError(f"Password hashing failed: {e}")


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
        raise RuntimeError(
            "Cannot verify token: authentication libraries not available or SECRET_KEY missing."
        )
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Validate the API Key for secured endpoints."""
    from app.config.settings import get_settings
    settings = get_settings()
    valid_keys = settings.VALID_API_KEYS
    if not api_key_header or api_key_header not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header

def verify_role(required_role: str):
    """RBAC middleware generator."""
    async def role_checker(api_key: str = Security(get_api_key)):
        if required_role == "admin" and api_key not in settings.VALID_API_KEYS:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True
    return role_checker