from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.llm.service import LLMService, LLMProcessingError
from app.services.document_ai.parser import DocumentAIService
from app.services.verification.engine import VerificationEngine

router = APIRouter(prefix="/document-ai", tags=["Document AI"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse a financial document (PDF, Excel, CSV) and extract structured loan data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50 MB.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "xlsx", "xls", "csv"):
        raise HTTPException(status_code=400, detail="Unsupported format. Use PDF, Excel (.xlsx/.xls), or CSV.")

    llm_service = LLMService(db)
    doc_service = DocumentAIService(llm_service)

    try:
        result = await doc_service.parse_document(
            org_id=user.organization_id,
            file_content=content,
            filename=file.filename,
            content_type=file.content_type or "",
        )
    except LLMProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "filename": file.filename,
        "loans_extracted": result["total_extracted"],
        "extraction_method": result["extraction_method"],
        "warnings": result["parsing_warnings"],
        "loans": result["loans"][:5],  # Preview first 5
        "total_loans": result["total_extracted"],
    }


@router.post("/parse-and-verify")
async def parse_and_verify(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse a document and immediately create a credit verification."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50 MB.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "xlsx", "xls", "csv"):
        raise HTTPException(status_code=400, detail="Unsupported format. Use PDF, Excel (.xlsx/.xls), or CSV.")

    llm_service = LLMService(db)
    doc_service = DocumentAIService(llm_service)

    try:
        result = await doc_service.parse_document(
            org_id=user.organization_id,
            file_content=content,
            filename=file.filename,
            content_type=file.content_type or "",
        )
    except LLMProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not result["loans"]:
        raise HTTPException(status_code=422, detail="No valid loans extracted from document")

    # Create verification
    engine = VerificationEngine(db)
    verification = await engine.create_verification(
        org_id=user.organization_id,
        user_id=user.id,
        module="private_credit",
        input_data={
            "loans": result["loans"],
            "portfolio_name": file.filename,
            "fund_name": "Document AI Import",
        },
        metadata={
            "source": "document_ai",
            "filename": file.filename,
            "extraction_method": result["extraction_method"],
            "loan_count": result["total_extracted"],
            "warnings": result["parsing_warnings"],
        },
    )
    await db.commit()

    from app.workers.verification_tasks import process_verification_task
    process_verification_task.delay(str(verification.id))

    return {
        "verification_id": str(verification.id),
        "filename": file.filename,
        "loans_extracted": result["total_extracted"],
        "extraction_method": result["extraction_method"],
        "warnings": result["parsing_warnings"],
        "status": "pending",
        "message": f"Extracted {result['total_extracted']} loans from {file.filename}. Verification queued.",
    }
