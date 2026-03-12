from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification, VerificationStatus, VerificationModule
from app.api.deps import get_current_user
from app.schemas.verification import VerificationCreate, VerificationResponse
from app.services.verification.engine import VerificationEngine
from app.services.verification.proof import ProofService
import math

router = APIRouter(prefix="/verifications", tags=["Verifications"])


@router.post("")
async def create_verification(
    data: VerificationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = VerificationEngine(db)
    verification = await engine.create_verification(
        org_id=user.organization_id,
        user_id=user.id,
        module=data.module,
        input_data=data.input_data,
        metadata=data.metadata,
    )
    await db.commit()

    # Dispatch to Celery for async processing
    from app.workers.verification_tasks import process_verification_task
    process_verification_task.delay(str(verification.id))

    return {
        "id": str(verification.id),
        "status": verification.status.value,
        "module": verification.module.value,
        "message": "Verification created and queued for processing",
    }


@router.get("")
async def list_verifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    module: str = Query(None),
    status: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Verification).where(
        Verification.organization_id == user.organization_id,
        Verification.is_deleted == False,
    )

    if module:
        query = query.where(Verification.module == VerificationModule(module))
    if status:
        query = query.where(Verification.status == VerificationStatus(status))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Verification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    verifications = result.scalars().all()

    return {
        "items": [
            {
                "id": str(v.id),
                "organization_id": str(v.organization_id),
                "created_by": str(v.created_by),
                "module": v.module.value,
                "status": v.status.value,
                "input_data": v.input_data,
                "result_data": v.result_data,
                "proof_hash": v.proof_hash,
                "proof_certificate_url": v.proof_certificate_url,
                "report_url": v.report_url,
                "metadata": v.extra_metadata,
                "error_message": v.error_message,
                "created_at": v.created_at,
                "completed_at": v.completed_at,
            }
            for v in verifications
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/{verification_id}")
async def get_verification(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.organization_id == user.organization_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    return {
        "id": str(v.id),
        "organization_id": str(v.organization_id),
        "created_by": str(v.created_by),
        "module": v.module.value,
        "status": v.status.value,
        "input_data": v.input_data,
        "result_data": v.result_data,
        "proof_hash": v.proof_hash,
        "proof_certificate_url": v.proof_certificate_url,
        "report_url": v.report_url,
        "metadata": v.extra_metadata,
        "error_message": v.error_message,
        "created_at": v.created_at,
        "completed_at": v.completed_at,
    }


@router.post("/{verification_id}/verify-proof")
async def verify_proof(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.organization_id == user.organization_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    if not v.proof_hash:
        raise HTTPException(status_code=400, detail="No proof available for this verification")

    is_valid = ProofService.verify_proof(
        proof_hash=v.proof_hash,
        inputs=v.input_data,
        outputs=v.result_data or {},
        computation_type=v.module.value,
    )

    return {
        "verification_id": str(v.id),
        "proof_hash": v.proof_hash,
        "is_valid": is_valid,
        "message": "Proof verified successfully" if is_valid else "Proof verification failed",
    }


@router.post("/{verification_id}/generate-report")
async def generate_executive_report(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an LLM-powered executive report for a completed verification."""
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.organization_id == user.organization_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    if v.status.value != "completed":
        raise HTTPException(status_code=400, detail="Verification must be completed to generate a report")
    if not v.result_data:
        raise HTTPException(status_code=400, detail="No result data available")

    from app.services.llm.service import LLMService
    from app.services.llm.report_generator import ReportGenerator

    llm_service = LLMService(db)
    report_gen = ReportGenerator(llm_service)

    if v.module.value == "private_credit":
        report = await report_gen.generate_credit_executive_report(
            user.organization_id, v.result_data
        )
    else:
        report = await report_gen.generate_aiip_executive_report(
            user.organization_id, v.result_data
        )

    # Store report in metadata
    updated_metadata = {**(v.extra_metadata or {}), "executive_report": report}
    v.extra_metadata = updated_metadata
    await db.flush()

    return {
        "verification_id": str(v.id),
        "report": report,
    }


@router.post("/{verification_id}/comparable-analysis")
async def generate_comparable_analysis(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate market comparable analysis for an AI-IP valuation."""
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.organization_id == user.organization_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    if v.module.value != "ai_ip_valuation":
        raise HTTPException(status_code=400, detail="Comparable analysis only available for AI-IP valuations")
    if not v.result_data:
        raise HTTPException(status_code=400, detail="No result data available")

    from app.services.llm.service import LLMService
    from app.services.valuation.market_comparables import MarketComparablesService

    llm_service = LLMService(db)
    comparables_service = MarketComparablesService(llm_service)

    analysis = await comparables_service.generate_comparable_analysis(
        user.organization_id,
        v.result_data,
        v.result_data.get("estimated_value", 0),
    )

    return {
        "verification_id": str(v.id),
        "analysis": analysis,
    }
