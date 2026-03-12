from sqlalchemy import Column, String, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.models.base import TimestampMixin
from app.core.database import Base


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
