
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session
from app.logs.logger import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

async def get_db(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        # Fallback or allow anonymous? No, we should return anonymous for optional routes
        # But for required routes, we need a RoleChecker
        return {"user_id": "anonymous", "role": "viewer"}
    try:
        from app.auth.security import verify_token
        user = verify_token(token)
        if user:
            return user
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
    return {"user_id": "anonymous", "role": "viewer"}

def require_role(allowed_roles: list[str]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker