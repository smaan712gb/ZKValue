from sqlalchemy import Column, String, Integer, Numeric, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin
from app.core.database import Base


class CreditPortfolio(TenantMixin, Base):
    __tablename__ = "credit_portfolios"

    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    portfolio_name = Column(String(255), nullable=False)
    fund_name = Column(String(255), nullable=False)
    loan_count = Column(Integer, default=0, nullable=False)
    total_principal = Column(Numeric(precision=18, scale=2), default=0.0, nullable=False)
    weighted_avg_rate = Column(Numeric(precision=10, scale=6), default=0.0, nullable=False)
    avg_ltv_ratio = Column(Numeric(precision=10, scale=6), default=0.0, nullable=False)
    nav_value = Column(Numeric(precision=18, scale=2), default=0.0, nullable=False)
    covenant_compliance_status = Column(JSON, default=dict, nullable=False)
    loan_tape_url = Column(Text, nullable=True)
