from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.llm.service import LLMService, LLMProcessingError
from app.services.regulatory.generator import RegulatoryReportGenerator

router = APIRouter(prefix="/regulatory", tags=["Regulatory Reports"])


@router.get("/form-pf")
async def generate_form_pf(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate SEC Form PF report from all portfolio data."""
    llm_service = LLMService(db)
    generator = RegulatoryReportGenerator(db, llm_service)
    try:
        return await generator.generate_form_pf(user.organization_id)
    except LLMProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/aifmd")
async def generate_aifmd_report(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AIFMD Annex IV report."""
    llm_service = LLMService(db)
    generator = RegulatoryReportGenerator(db, llm_service)
    try:
        return await generator.generate_aifmd_annex_iv(user.organization_id)
    except LLMProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/narrative/{report_type}")
async def generate_narrative(
    report_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate LLM-powered compliance narrative for a regulatory report."""
    llm_service = LLMService(db)
    generator = RegulatoryReportGenerator(db, llm_service)

    if report_type == "form-pf":
        report_data = await generator.generate_form_pf(user.organization_id)
    elif report_type == "aifmd":
        report_data = await generator.generate_aifmd_annex_iv(user.organization_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}. Use 'form-pf' or 'aifmd'.")

    narrative = await generator.generate_regulatory_narrative(user.organization_id, report_data)

    return {
        "report_type": report_type,
        "report_data": report_data,
        "narrative": narrative,
    }
