import enum
from sqlalchemy import Column, String, Integer, Enum, JSON, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin
from app.core.database import Base


class ModelProvider(str, enum.Enum):
    deepseek = "deepseek"
    openai = "openai"
    anthropic = "anthropic"
    custom = "custom"


class LineageEventType(str, enum.Enum):
    data_ingestion = "data_ingestion"
    preprocessing = "preprocessing"
    llm_classification = "llm_classification"
    llm_analysis = "llm_analysis"
    computation = "computation"
    proof_generation = "proof_generation"
    report_generation = "report_generation"
    anomaly_detection = "anomaly_detection"
    valuation = "valuation"


class ModelUsageRecord(TenantMixin, Base):
    __tablename__ = "model_usage_records"

    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    provider = Column(Enum(ModelProvider), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    operation = Column(String(100), nullable=False)  # classify_asset, analyze_loan_tape, etc.
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    prompt_hash = Column(String(64), nullable=True)  # SHA-256 of system prompt for reproducibility
    response_hash = Column(String(64), nullable=True)  # SHA-256 of response
    cost_usd = Column(Float, default=0.0, nullable=False)
    success = Column(String(10), default="true", nullable=False)  # true, false, error
    error_message = Column(Text, nullable=True)


class DataLineageEvent(TenantMixin, Base):
    __tablename__ = "data_lineage_events"

    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    event_type = Column(Enum(LineageEventType), nullable=False)
    step_order = Column(Integer, nullable=False)  # Sequential order in the pipeline
    input_hash = Column(String(64), nullable=False)  # SHA-256 of input data
    output_hash = Column(String(64), nullable=False)  # SHA-256 of output data
    transformation = Column(String(255), nullable=False)  # Description of what happened
    details = Column(JSON, default=dict, nullable=False)  # Additional context
    duration_ms = Column(Integer, default=0, nullable=False)
    parent_event_id = Column(UUID(as_uuid=True), ForeignKey("data_lineage_events.id"), nullable=True)
