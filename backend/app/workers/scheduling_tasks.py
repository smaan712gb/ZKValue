import asyncio
import logging
from datetime import datetime, timezone
from app.workers.celery_app import celery_app
from app.workers.verification_tasks import _make_session_factory

logger = logging.getLogger(__name__)


@celery_app.task
def process_due_schedules():
    """Find and execute all verification schedules that are due."""
    logger.info("Checking for due verification schedules")

    async def _process():
        from app.services.scheduling.scheduler import SchedulerService
        from app.services.notifications.service import NotificationService

        session_factory, engine = _make_session_factory()
        try:
            async with session_factory() as session:
                scheduler = SchedulerService(session)
                notification_service = NotificationService(session)
                due_schedules = await scheduler.get_due_schedules()

                logger.info(f"Found {len(due_schedules)} due schedules")

                for schedule in due_schedules:
                    try:
                        verification_id = await scheduler.execute_schedule(schedule)
                        logger.info(f"Schedule '{schedule.name}' executed: verification {verification_id}")

                        await notification_service.create_notification(
                            org_id=schedule.organization_id,
                            notification_type="schedule_executed",
                            title=f"Scheduled Verification: {schedule.name}",
                            message=f"Scheduled {schedule.frequency.value} verification completed.",
                            reference_id=verification_id,
                            reference_type="verification",
                        )
                    except Exception as e:
                        logger.error(f"Failed to execute schedule '{schedule.name}': {e}")

                await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(_process())


@celery_app.task
def generate_all_usage_reports():
    """Generate usage reports for all active organizations."""
    logger.info("Generating monthly usage reports for all organizations")

    async def _generate():
        from sqlalchemy import select
        from app.models.organization import Organization

        now = datetime.now(timezone.utc)
        month_str = f"{now.year}-{now.month:02d}"

        session_factory, engine = _make_session_factory()
        try:
            async with session_factory() as session:
                result = await session.execute(
                    select(Organization).where(Organization.is_active == True)
                )
                orgs = result.scalars().all()

                for org in orgs:
                    from app.workers.report_tasks import generate_usage_report
                    generate_usage_report.delay(str(org.id), month_str)

                logger.info(f"Dispatched usage reports for {len(orgs)} organizations")
        finally:
            await engine.dispose()

    asyncio.run(_generate())
