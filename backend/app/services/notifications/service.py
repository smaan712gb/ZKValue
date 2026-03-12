import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationPreference, NotificationType, NotificationChannel
from app.models.schedule import DriftAlert

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self,
        org_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        user_id: Optional[UUID] = None,
        details: Optional[dict] = None,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> Notification:
        """Create an in-app notification."""
        notification = Notification(
            organization_id=org_id,
            user_id=user_id,
            notification_type=notification_type,
            channel=NotificationChannel.in_app,
            title=title,
            message=message,
            details=details or {},
            reference_id=reference_id,
            reference_type=reference_type,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def notify_verification_completed(self, org_id: UUID, verification_id: str, module: str, metadata: dict):
        """Send notification when a verification completes."""
        name = metadata.get("portfolio_name") or metadata.get("asset_name") or verification_id
        module_label = "Credit" if module == "private_credit" else "AI-IP"
        await self.create_notification(
            org_id=org_id,
            notification_type=NotificationType.verification_completed,
            title=f"{module_label} Verification Complete",
            message=f"Verification for '{name}' completed successfully with cryptographic proof.",
            reference_id=verification_id,
            reference_type="verification",
        )

    async def notify_verification_failed(self, org_id: UUID, verification_id: str, error: str, metadata: dict):
        """Send notification when a verification fails."""
        name = metadata.get("portfolio_name") or metadata.get("asset_name") or verification_id
        await self.create_notification(
            org_id=org_id,
            notification_type=NotificationType.verification_failed,
            title="Verification Failed",
            message=f"Verification for '{name}' failed: {error[:200]}",
            reference_id=verification_id,
            reference_type="verification",
        )

    async def notify_drift_alert(self, org_id: UUID, alert: DriftAlert):
        """Send notification for a drift alert."""
        severity_label = alert.severity.value.upper()
        await self.create_notification(
            org_id=org_id,
            notification_type=NotificationType.drift_alert,
            title=f"[{severity_label}] {alert.alert_type.replace('_', ' ').title()}",
            message=alert.message,
            details=alert.details,
            reference_id=str(alert.id),
            reference_type="drift_alert",
        )

    async def notify_usage_limit(self, org_id: UUID, current_usage: int, limit: int):
        """Send warning when approaching usage limit."""
        pct = int(current_usage / limit * 100)
        await self.create_notification(
            org_id=org_id,
            notification_type=NotificationType.usage_limit_warning,
            title="Usage Limit Warning",
            message=f"You've used {current_usage} of {limit} monthly verifications ({pct}%). Consider upgrading your plan.",
            details={"current_usage": current_usage, "limit": limit, "percentage": pct},
        )

    async def get_unread_notifications(self, org_id: UUID, user_id: UUID, limit: int = 20) -> list[Notification]:
        """Get unread notifications for a user."""
        from sqlalchemy import or_
        result = await self.session.execute(
            select(Notification).where(
                Notification.organization_id == org_id,
                Notification.is_deleted == False,
                Notification.is_read == False,
                or_(Notification.user_id == user_id, Notification.user_id == None),
            ).order_by(Notification.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_notifications(self, org_id: UUID, user_id: UUID, page: int = 1, page_size: int = 50) -> tuple[list[Notification], int]:
        """Get all notifications with pagination."""
        from sqlalchemy import or_, func
        base = select(Notification).where(
            Notification.organization_id == org_id,
            Notification.is_deleted == False,
            or_(Notification.user_id == user_id, Notification.user_id == None),
        )
        count = (await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        result = await self.session.execute(
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), count

    async def mark_as_read(self, notification_id: UUID, user_id: UUID):
        """Mark a notification as read."""
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )

    async def mark_all_as_read(self, org_id: UUID, user_id: UUID):
        """Mark all notifications as read for a user."""
        from sqlalchemy import or_
        await self.session.execute(
            update(Notification)
            .where(
                Notification.organization_id == org_id,
                Notification.is_read == False,
                or_(Notification.user_id == user_id, Notification.user_id == None),
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
