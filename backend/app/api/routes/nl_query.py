from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.llm.service import LLMService, LLMProcessingError
from app.services.nl_query.engine import NLQueryEngine

router = APIRouter(prefix="/nl-query", tags=["Natural Language Queries"])


class NLQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    max_rows: int = Field(50, ge=1, le=200)


@router.post("")
async def ask_question(
    request: NLQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask a natural language question about your verification data."""
    llm_service = LLMService(db)
    engine = NLQueryEngine(db, llm_service)

    try:
        result = await engine.query(
            org_id=user.organization_id,
            question=request.question,
            max_rows=request.max_rows,
        )
    except LLMProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result


@router.get("/suggestions")
async def get_suggestions(
    user: User = Depends(get_current_user),
):
    """Get suggested questions."""
    engine = NLQueryEngine.__new__(NLQueryEngine)
    return {
        "suggestions": await engine.get_suggested_questions(),
    }
