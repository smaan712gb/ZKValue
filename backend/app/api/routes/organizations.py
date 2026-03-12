from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.api.deps import get_current_user, get_current_org, require_role
from app.schemas.auth import LLMConfigUpdate, OrgUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current")
async def get_current_organization(org: Organization = Depends(get_current_org)):
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "domain": org.domain,
        "plan": org.plan.value,
        "llm_provider": org.llm_provider,
        "llm_model": org.llm_model,
        "max_verifications_per_month": org.max_verifications_per_month,
        "is_active": org.is_active,
        "settings": org.settings,
        "created_at": org.created_at,
    }


@router.put("/current")
async def update_organization(
    data: OrgUpdate,
    user: User = Depends(require_role(["owner", "admin"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    if data.name:
        org.name = data.name
    if data.domain is not None:
        org.domain = data.domain
    if data.settings is not None:
        org.settings = data.settings
    await db.flush()
    return {"message": "Organization updated"}


@router.put("/current/llm-config")
async def update_llm_config(
    data: LLMConfigUpdate,
    user: User = Depends(require_role(["owner", "admin"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    valid_providers = ["deepseek", "openai", "anthropic"]
    if data.llm_provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Choose from: {valid_providers}")

    org.llm_provider = data.llm_provider
    org.llm_model = data.llm_model
    await db.flush()
    return {"message": "LLM configuration updated", "provider": data.llm_provider, "model": data.llm_model}


@router.get("/current/members")
async def list_members(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.organization_id == user.organization_id,
            User.is_deleted == False,
        )
    )
    members = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "email": m.email,
            "full_name": m.full_name,
            "role": m.role.value,
            "is_active": m.is_active,
            "last_login": m.last_login,
            "created_at": m.created_at,
        }
        for m in members
    ]


@router.delete("/current/members/{user_id}")
async def remove_member(
    user_id: str,
    user: User = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == user.organization_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role.value == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")

    member.is_active = False
    member.is_deleted = True
    await db.flush()
    return {"message": "Member removed"}
