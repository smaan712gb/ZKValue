import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.api.deps import get_current_user
import math

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    user_id: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).where(AuditLog.organization_id == user.organization_id)

    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "timestamp": log.timestamp,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/export")
async def export_audit_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value not in ["owner", "admin"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only owners and admins can export audit logs")
    """Export audit logs as CSV."""
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.organization_id == user.organization_id
        ).order_by(AuditLog.timestamp.desc()).limit(10000)
    )
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "User ID", "Action", "Resource Type", "Resource ID", "Details", "IP Address"])

    for log in logs:
        writer.writerow([
            str(log.timestamp),
            str(log.user_id) if log.user_id else "",
            log.action,
            log.resource_type,
            log.resource_id or "",
            str(log.details),
            log.ip_address or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
