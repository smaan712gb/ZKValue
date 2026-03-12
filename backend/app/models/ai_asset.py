import enum
from sqlalchemy import Column, String, Numeric, Boolean, Enum, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin
from app.core.database import Base


class AssetType(str, enum.Enum):
    training_data = "training_data"
    model_weights = "model_weights"
    inference_infra = "inference_infra"
    deployed_app = "deployed_app"


class ValuationMethod(str, enum.Enum):
    cost_approach = "cost_approach"
    market_approach = "market_approach"
    income_approach = "income_approach"


class AIAsset(TenantMixin, Base):
    __tablename__ = "ai_assets"

    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    valuation_method = Column(Enum(ValuationMethod), nullable=False)
    estimated_value = Column(Numeric(precision=18, scale=2), default=0.0, nullable=False)
    confidence_score = Column(Numeric(precision=5, scale=4), default=0.0, nullable=False)
    valuation_inputs = Column(JSON, default=dict, nullable=False)
    valuation_breakdown = Column(JSON, default=dict, nullable=False)
    ias38_compliant = Column(Boolean, default=False, nullable=False)
    asc350_compliant = Column(Boolean, default=False, nullable=False)
