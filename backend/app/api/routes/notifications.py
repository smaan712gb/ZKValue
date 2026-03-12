import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifications, total = await service.get_all_notifications(
        user.organization_id, user.id, page, page_size
    )
    return {
        "items": [
            {
                "id": str(n.id),
                "notification_type": n.notification_type.value,
                "title": n.title,
                "message": n.message,
                "details": n.details,
                "is_read": n.is_read,
                "read_at": n.read_at,
                "reference_id": n.reference_id,
                "reference_type": n.reference_type,
                "created_at": n.created_at,
            }
            for n in notifications
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/unread")
async def get_unread_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifications = await service.get_unread_notifications(user.organization_id, user.id)
    return {
        "count": len(notifications),
        "items": [
            {
                "id": str(n.id),
                "notification_type": n.notification_type.value,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "reference_id": n.reference_id,
                "reference_type": n.reference_type,
                "created_at": n.created_at,
            }
            for n in notifications
        ],
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_as_read(notification_id, user.id)
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_all_as_read(user.organization_id, user.id)
    return {"message": "All notifications marked as read"}
