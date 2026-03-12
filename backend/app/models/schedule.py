import enum
from sqlalchemy import Column, String, Boolean, Integer, Enum, JSON, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin
from app.core.database import Base


class ScheduleFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class VerificationSchedule(TenantMixin, Base):
    __tablename__ = "verification_schedules"

    name = Column(String(255), nullable=False)
    module = Column(String(50), nullable=False)  # private_credit or ai_ip_valuation
    frequency = Column(Enum(ScheduleFrequency), nullable=False)
    input_data = Column(JSON, default=dict, nullable=False)
    extra_metadata = Column("metadata", JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    drift_threshold_pct = Column(Numeric(5, 2), default=10.0, nullable=False)  # Alert if value changes > X%
    last_verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=True)
    run_count = Column(Integer, default=0, nullable=False)


class DriftAlert(TenantMixin, Base):
    __tablename__ = "drift_alerts"

    schedule_id = Column(UUID(as_uuid=True), ForeignKey("verification_schedules.id"), nullable=False)
    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    previous_verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.active, nullable=False)
    alert_type = Column(String(100), nullable=False)  # nav_drift, ltv_breach, covenant_violation, value_change
    message = Column(String(1000), nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    drift_pct = Column(Numeric(10, 4), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
