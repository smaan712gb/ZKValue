from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification, VerificationStatus, VerificationModule
from app.models.credit_portfolio import CreditPortfolio
from app.models.ai_asset import AIAsset
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = user.organization_id

    # Verification counts
    total = (await db.execute(
        select(func.count()).where(Verification.organization_id == org_id, Verification.is_deleted == False)
    )).scalar() or 0

    completed = (await db.execute(
        select(func.count()).where(
            Verification.organization_id == org_id,
            Verification.status == VerificationStatus.completed,
            Verification.is_deleted == False,
        )
    )).scalar() or 0

    pending = (await db.execute(
        select(func.count()).where(
            Verification.organization_id == org_id,
            Verification.status.in_([VerificationStatus.pending, VerificationStatus.processing]),
            Verification.is_deleted == False,
        )
    )).scalar() or 0

    failed = (await db.execute(
        select(func.count()).where(
            Verification.organization_id == org_id,
            Verification.status == VerificationStatus.failed,
            Verification.is_deleted == False,
        )
    )).scalar() or 0

    # Credit portfolios
    credit_count = (await db.execute(
        select(func.count()).where(CreditPortfolio.organization_id == org_id, CreditPortfolio.is_deleted == False)
    )).scalar() or 0

    credit_value = (await db.execute(
        select(func.sum(CreditPortfolio.nav_value)).where(
            CreditPortfolio.organization_id == org_id, CreditPortfolio.is_deleted == False
        )
    )).scalar() or 0

    # AI Assets
    ai_count = (await db.execute(
        select(func.count()).where(AIAsset.organization_id == org_id, AIAsset.is_deleted == False)
    )).scalar() or 0

    ai_value = (await db.execute(
        select(func.sum(AIAsset.estimated_value)).where(
            AIAsset.organization_id == org_id, AIAsset.is_deleted == False
        )
    )).scalar() or 0

    # Recent verifications
    recent_result = await db.execute(
        select(Verification).where(
            Verification.organization_id == org_id, Verification.is_deleted == False
        ).order_by(Verification.created_at.desc()).limit(10)
    )
    recent = recent_result.scalars().all()

    return {
        "total_verifications": total,
        "completed_verifications": completed,
        "pending_verifications": pending,
        "failed_verifications": failed,
        "total_asset_value": float(credit_value + ai_value),
        "credit_portfolios": credit_count,
        "ai_assets": ai_count,
        "monthly_usage": (await db.execute(
            select(func.count()).where(
                Verification.organization_id == org_id,
                Verification.is_deleted == False,
                extract("month", Verification.created_at) == datetime.now(timezone.utc).month,
                extract("year", Verification.created_at) == datetime.now(timezone.utc).year,
            )
        )).scalar() or 0,  # Current month only
        "monthly_limit": user.organization.max_verifications_per_month if user.organization else 10,
        "recent_verifications": [
            {
                "id": str(v.id),
                "module": v.module.value,
                "status": v.status.value,
                "metadata": v.extra_metadata,
                "created_at": v.created_at,
                "completed_at": v.completed_at,
            }
            for v in recent
        ],
        "value_by_module": [
            {"module": "Private Credit", "value": float(credit_value)},
            {"module": "AI-IP Valuation", "value": float(ai_value)},
        ],
    }


@router.get("/recent-activity")
async def get_recent_activity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification).where(
            Verification.organization_id == user.organization_id,
            Verification.is_deleted == False,
        ).order_by(Verification.created_at.desc()).limit(20)
    )
    verifications = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "module": v.module.value,
            "status": v.status.value,
            "metadata": v.extra_metadata,
            "created_at": v.created_at,
        }
        for v in verifications
    ]
