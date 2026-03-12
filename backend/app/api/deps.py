from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.organization import Organization
from app.services.llm.service import LLMService
from typing import List

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


async def get_current_org(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
    org = result.scalar_one_or_none()
    if not org or not org.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization not active")
    return org


def require_role(allowed_roles: List[str]):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' not authorized. Required: {allowed_roles}",
            )
        return user
    return role_checker


async def get_llm_service(db: AsyncSession = Depends(get_db)) -> LLMService:
    return LLMService(db)
