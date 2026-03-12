from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.ai_asset import AIAsset
from app.api.deps import get_current_user, get_llm_service
from app.services.verification.engine import VerificationEngine
from app.services.llm.service import LLMService
from app.schemas.verification import AIIPValuationInput

router = APIRouter(prefix="/ai-ip", tags=["AI-IP Valuation"])


@router.post("/classify")
async def classify_asset(
    data: AIIPValuationInput,
    user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Classify an AI asset using LLM analysis."""
    classification = await llm_service.classify_asset(
        user.organization_id, data.description
    )
    return {
        "asset_name": data.asset_name,
        "classification": classification,
    }


@router.post("/valuate")
async def valuate_asset(
    data: AIIPValuationInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an AI-IP valuation."""
    engine = VerificationEngine(db)
    verification = await engine.create_verification(
        org_id=user.organization_id,
        user_id=user.id,
        module="ai_ip_valuation",
        input_data=data.model_dump(exclude_none=True),
        metadata={"asset_name": data.asset_name, "asset_type": data.asset_type},
    )
    await db.commit()

    return {
        "verification_id": str(verification.id),
        "status": "pending",
        "message": "AI-IP valuation queued.",
    }


@router.get("/assets")
async def list_assets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIAsset).where(
            AIAsset.organization_id == user.organization_id,
            AIAsset.is_deleted == False,
        ).order_by(AIAsset.created_at.desc())
    )
    assets = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "verification_id": str(a.verification_id),
            "asset_type": a.asset_type.value,
            "asset_name": a.asset_name,
            "description": a.description,
            "valuation_method": a.valuation_method.value,
            "estimated_value": a.estimated_value,
            "confidence_score": a.confidence_score,
            "valuation_inputs": a.valuation_inputs,
            "valuation_breakdown": a.valuation_breakdown,
            "ias38_compliant": a.ias38_compliant,
            "asc350_compliant": a.asc350_compliant,
            "created_at": a.created_at,
        }
        for a in assets
    ]


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIAsset).where(
            AIAsset.id == asset_id,
            AIAsset.organization_id == user.organization_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {
        "id": str(a.id),
        "verification_id": str(a.verification_id),
        "asset_type": a.asset_type.value,
        "asset_name": a.asset_name,
        "description": a.description,
        "valuation_method": a.valuation_method.value,
        "estimated_value": a.estimated_value,
        "confidence_score": a.confidence_score,
        "valuation_inputs": a.valuation_inputs,
        "valuation_breakdown": a.valuation_breakdown,
        "ias38_compliant": a.ias38_compliant,
        "asc350_compliant": a.asc350_compliant,
        "created_at": a.created_at,
    }
