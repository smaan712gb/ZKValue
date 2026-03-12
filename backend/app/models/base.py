import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class TimestampMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_deleted = Column(Boolean, default=False, nullable=False)


class TenantMixin(TimestampMixin):
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
