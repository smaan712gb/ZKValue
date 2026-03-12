from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.registry.service import ModelRegistryService

router = APIRouter(prefix="/model-registry", tags=["Model Registry & Lineage"])


@router.get("/lineage/{verification_id}")
async def get_verification_lineage(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete data lineage and model usage for a verification."""
    service = ModelRegistryService(db)
    return await service.get_verification_lineage(
        user.organization_id, verification_id
    )


@router.get("/stats")
async def get_model_stats(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated model usage statistics."""
    service = ModelRegistryService(db)
    return await service.get_org_model_stats(user.organization_id, days)
