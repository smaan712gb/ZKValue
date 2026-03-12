import enum
from sqlalchemy import Column, String, Enum, JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TenantMixin
from app.core.database import Base


class VerificationModule(str, enum.Enum):
    private_credit = "private_credit"
    ai_ip_valuation = "ai_ip_valuation"


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Verification(TenantMixin, Base):
    __tablename__ = "verifications"

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    module = Column(Enum(VerificationModule), nullable=False, index=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.pending, nullable=False, index=True)
    input_data = Column(JSON, default=dict, nullable=False)
    result_data = Column(JSON, nullable=True)
    proof_hash = Column(String(255), nullable=True)
    proof_certificate_url = Column(Text, nullable=True)
    report_url = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", lazy="joined")
