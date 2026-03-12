import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Literal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.schedule import VerificationSchedule, DriftAlert, ScheduleFrequency, AlertStatus
from app.api.deps import get_current_user, require_role
from app.services.scheduling.scheduler import SchedulerService

router = APIRouter(prefix="/schedules", tags=["Schedules"])


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    module: Literal["private_credit", "ai_ip_valuation"]
    frequency: Literal["daily", "weekly", "monthly", "quarterly"]
    input_data: dict
    metadata: Optional[dict] = None
    drift_threshold_pct: float = Field(default=10.0, ge=1.0, le=100.0)


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[Literal["daily", "weekly", "monthly", "quarterly"]] = None
    is_active: Optional[bool] = None
    drift_threshold_pct: Optional[float] = Field(default=None, ge=1.0, le=100.0)


@router.post("")
async def create_schedule(
    data: ScheduleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scheduler = SchedulerService(db)
    freq = ScheduleFrequency(data.frequency)
    schedule = VerificationSchedule(
        organization_id=user.organization_id,
        name=data.name,
        module=data.module,
        frequency=freq,
        input_data=data.input_data,
        extra_metadata=data.metadata or {},
        created_by=user.id,
        drift_threshold_pct=data.drift_threshold_pct,
        next_run_at=scheduler.calculate_next_run(freq),
    )
    db.add(schedule)
    await db.flush()
    return {
        "id": str(schedule.id),
        "name": schedule.name,
        "next_run_at": schedule.next_run_at,
        "message": "Schedule created successfully",
    }


@router.get("")
async def list_schedules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VerificationSchedule).where(
            VerificationSchedule.organization_id == user.organization_id,
            VerificationSchedule.is_deleted == False,
        ).order_by(VerificationSchedule.created_at.desc())
    )
    schedules = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "module": s.module,
            "frequency": s.frequency.value,
            "is_active": s.is_active,
            "last_run_at": s.last_run_at,
            "next_run_at": s.next_run_at,
            "run_count": s.run_count,
            "drift_threshold_pct": float(s.drift_threshold_pct),
            "created_at": s.created_at,
        }
        for s in schedules
    ]


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    data: ScheduleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VerificationSchedule).where(
            VerificationSchedule.id == schedule_id,
            VerificationSchedule.organization_id == user.organization_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if data.name is not None:
        schedule.name = data.name
    if data.frequency is not None:
        schedule.frequency = ScheduleFrequency(data.frequency)
        scheduler = SchedulerService(db)
        schedule.next_run_at = scheduler.calculate_next_run(schedule.frequency)
    if data.is_active is not None:
        schedule.is_active = data.is_active
    if data.drift_threshold_pct is not None:
        schedule.drift_threshold_pct = data.drift_threshold_pct
    await db.flush()
    return {"message": "Schedule updated"}


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VerificationSchedule).where(
            VerificationSchedule.id == schedule_id,
            VerificationSchedule.organization_id == user.organization_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.is_deleted = True
    schedule.is_active = False
    await db.flush()
    return {"message": "Schedule deleted"}


@router.post("/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: str,
    user: User = Depends(require_role(["owner", "admin", "analyst"])),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a scheduled verification."""
    result = await db.execute(
        select(VerificationSchedule).where(
            VerificationSchedule.id == schedule_id,
            VerificationSchedule.organization_id == user.organization_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    scheduler = SchedulerService(db)
    verification_id = await scheduler.execute_schedule(schedule)
    await db.commit()
    return {
        "message": "Schedule executed",
        "verification_id": verification_id,
    }


@router.get("/alerts")
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DriftAlert).where(
        DriftAlert.organization_id == user.organization_id,
        DriftAlert.is_deleted == False,
    )
    if severity:
        query = query.where(DriftAlert.severity == severity)
    if status:
        query = query.where(DriftAlert.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(DriftAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "items": [
            {
                "id": str(a.id),
                "schedule_id": str(a.schedule_id),
                "verification_id": str(a.verification_id),
                "severity": a.severity.value,
                "status": a.status.value,
                "alert_type": a.alert_type,
                "message": a.message,
                "details": a.details,
                "drift_pct": float(a.drift_pct) if a.drift_pct else None,
                "created_at": a.created_at,
                "acknowledged_at": a.acknowledged_at,
            }
            for a in alerts
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DriftAlert).where(
            DriftAlert.id == alert_id,
            DriftAlert.organization_id == user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.acknowledged
    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": "Alert acknowledged"}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DriftAlert).where(
            DriftAlert.id == alert_id,
            DriftAlert.organization_id == user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.resolved
    await db.flush()
    return {"message": "Alert resolved"}
