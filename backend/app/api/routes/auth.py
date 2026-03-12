import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
    generate_invite_token,
)
from app.models.user import User, UserRole
from app.models.organization import Organization, OrgPlan
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, UserInvite, OrganizationResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_]+", "-", slug)


def _user_response(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "last_login": user.last_login,
        "mfa_enabled": user.mfa_enabled,
        "organization": {
            "id": str(user.organization.id),
            "name": user.organization.name,
            "slug": user.organization.slug,
            "domain": user.organization.domain,
            "plan": user.organization.plan.value,
            "llm_provider": user.organization.llm_provider,
            "llm_model": user.organization.llm_model,
            "max_verifications_per_month": user.organization.max_verifications_per_month,
            "is_active": user.organization.is_active,
            "created_at": user.organization.created_at,
        },
        "created_at": user.created_at,
    }


@router.post("/register", response_model=Token)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Validate password strength
    is_valid, message = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if org slug is taken
    slug = _slugify(data.org_name)
    if not slug:
        raise HTTPException(status_code=400, detail="Organization name must contain alphanumeric characters")
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp()) % 10000}"

    # Create organization
    org = Organization(
        name=data.org_name,
        slug=slug,
        plan=OrgPlan.starter,
        llm_provider="deepseek",
        llm_model="deepseek-chat",
        max_verifications_per_month=10,
    )
    db.add(org)
    await db.flush()

    # Create user as owner
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        organization_id=org.id,
        role=UserRole.owner,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"user_id": str(user.id), "org_id": str(org.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Reject users who haven't set their password (invite-only accounts)
    if user.hashed_password.startswith("$INVITE$"):
        raise HTTPException(status_code=403, detail="Please use your invitation link to set a password first")

    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    token = create_access_token({"user_id": str(user.id), "org_id": str(user.organization_id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return _user_response(user)


@router.post("/invite")
async def invite_user(
    data: UserInvite,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can invite users")

    # Schema Literal already restricts to admin/analyst/viewer (no owner)

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate a secure invite token instead of a hardcoded password
    invite_token = generate_invite_token()

    new_user = User(
        email=data.email,
        # Store invite token as a marker — not a valid bcrypt hash, so login is blocked
        hashed_password=f"$INVITE${invite_token}",
        full_name=data.full_name,
        organization_id=user.organization_id,
        role=UserRole(data.role),
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    return {
        "message": f"Invitation created for {data.email}",
        "user_id": str(new_user.id),
        "invite_token": invite_token,
        "invite_url": f"/invite/accept?token={invite_token}",
    }


@router.post("/invite/accept")
async def accept_invite(
    token: str,
    password: str,
    db: AsyncSession = Depends(get_db),
):
    """Accept an invitation and set a password."""
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    result = await db.execute(
        select(User).where(User.hashed_password == f"$INVITE${token}")
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    user.hashed_password = get_password_hash(password)
    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(user)

    access_token = create_access_token({
        "user_id": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role.value,
    })

    return {"access_token": access_token, "token_type": "bearer", "user": _user_response(user)}
