import enum
from sqlalchemy import Column, String, Boolean, Enum, JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin
from app.core.database import Base


class NotificationChannel(str, enum.Enum):
    in_app = "in_app"
    email = "email"
    webhook = "webhook"
    slack = "slack"


class NotificationType(str, enum.Enum):
    verification_completed = "verification_completed"
    verification_failed = "verification_failed"
    drift_alert = "drift_alert"
    covenant_breach = "covenant_breach"
    usage_limit_warning = "usage_limit_warning"
    schedule_executed = "schedule_executed"


class Notification(TenantMixin, Base):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null = org-wide
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.in_app, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    reference_id = Column(String(255), nullable=True)  # ID of related object (verification, alert, etc.)
    reference_type = Column(String(50), nullable=True)  # Type of related object


class NotificationPreference(TenantMixin, Base):
    __tablename__ = "notification_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    webhook_url = Column(String(1000), nullable=True)
    slack_webhook_url = Column(String(1000), nullable=True)
    email_address = Column(String(255), nullable=True)
