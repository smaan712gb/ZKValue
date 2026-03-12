from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.credit_portfolio import CreditPortfolio
from app.models.verification import Verification, VerificationModule, VerificationStatus
from app.api.deps import get_current_user
from app.services.verification.engine import VerificationEngine
from app.schemas.verification import CreditVerificationInput
import json
import csv
import io

router = APIRouter(prefix="/credit", tags=["Private Credit"])


@router.post("/upload-loan-tape")
async def upload_loan_tape(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a loan tape file (CSV, JSON, or XLSX)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Enforce 50 MB file size limit
    MAX_FILE_SIZE = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50 MB.")
    loans = []

    if file.filename.endswith(".json"):
        data = json.loads(content)
        loans = data if isinstance(data, list) else data.get("loans", [])
    elif file.filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        loans = [dict(row) for row in reader]
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or JSON.")

    if not loans:
        raise HTTPException(status_code=400, detail="No loans found in the file")

    # Create verification
    engine = VerificationEngine(db)
    verification = await engine.create_verification(
        org_id=user.organization_id,
        user_id=user.id,
        module="private_credit",
        input_data={"loans": loans, "portfolio_name": file.filename, "fund_name": "Uploaded Portfolio"},
        metadata={"source": "file_upload", "filename": file.filename, "loan_count": len(loans)},
    )
    await db.commit()

    return {
        "verification_id": str(verification.id),
        "loan_count": len(loans),
        "status": "pending",
        "message": "Loan tape uploaded. Verification queued.",
    }


@router.post("/verify")
async def verify_credit(
    data: CreditVerificationInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a credit portfolio verification."""
    engine = VerificationEngine(db)
    verification = await engine.create_verification(
        org_id=user.organization_id,
        user_id=user.id,
        module="private_credit",
        input_data=data.model_dump(),
        metadata={"portfolio_name": data.portfolio_name, "fund_name": data.fund_name},
    )
    await db.commit()

    from app.workers.verification_tasks import process_verification_task
    process_verification_task.delay(str(verification.id))

    return {
        "verification_id": str(verification.id),
        "status": "pending",
        "message": "Credit verification queued.",
    }


@router.get("/portfolios")
async def list_portfolios(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditPortfolio).where(
            CreditPortfolio.organization_id == user.organization_id,
            CreditPortfolio.is_deleted == False,
        ).order_by(CreditPortfolio.created_at.desc())
    )
    portfolios = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "verification_id": str(p.verification_id),
            "portfolio_name": p.portfolio_name,
            "fund_name": p.fund_name,
            "loan_count": p.loan_count,
            "total_principal": p.total_principal,
            "weighted_avg_rate": p.weighted_avg_rate,
            "avg_ltv_ratio": p.avg_ltv_ratio,
            "nav_value": p.nav_value,
            "covenant_compliance_status": p.covenant_compliance_status,
            "created_at": p.created_at,
        }
        for p in portfolios
    ]


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(
    portfolio_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditPortfolio).where(
            CreditPortfolio.id == portfolio_id,
            CreditPortfolio.organization_id == user.organization_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return {
        "id": str(p.id),
        "verification_id": str(p.verification_id),
        "portfolio_name": p.portfolio_name,
        "fund_name": p.fund_name,
        "loan_count": p.loan_count,
        "total_principal": p.total_principal,
        "weighted_avg_rate": p.weighted_avg_rate,
        "avg_ltv_ratio": p.avg_ltv_ratio,
        "nav_value": p.nav_value,
        "covenant_compliance_status": p.covenant_compliance_status,
        "created_at": p.created_at,
    }
