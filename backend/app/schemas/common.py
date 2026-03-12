from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional
from datetime import datetime

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime
