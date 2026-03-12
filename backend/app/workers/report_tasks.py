import asyncio
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

ALLOWED_WEBHOOK_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254", "metadata.google.internal"}


def _validate_webhook_url(url: str) -> bool:
    """Validate webhook URL to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_WEBHOOK_SCHEMES:
            return False
        hostname = parsed.hostname or ""
        if hostname in BLOCKED_HOSTS:
            return False
        # Block private IP ranges
        if hostname.startswith(("10.", "192.168.", "172.")):
            return False
        return True
    except Exception:
        return False


@celery_app.task(bind=True, max_retries=2)
def send_webhook_notification(self, webhook_url: str, payload: dict):
    """Send webhook notification on verification completion."""
    import httpx

    if not _validate_webhook_url(webhook_url):
        logger.warning(f"Blocked webhook to disallowed URL: {webhook_url}")
        return

    logger.info(f"Sending webhook to {webhook_url}")
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
        logger.info(f"Webhook sent successfully to {webhook_url}")
    except Exception as exc:
        logger.error(f"Webhook delivery failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def cleanup_old_verifications(days: int = 90):
    """Cleanup old verification data beyond retention period."""
    logger.info(f"Cleaning up verifications older than {days} days")

    async def _cleanup():
        from sqlalchemy import update
        from app.core.database import async_session_factory
        from app.models.verification import Verification

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with async_session_factory() as session:
            result = await session.execute(
                update(Verification)
                .where(Verification.created_at < cutoff, Verification.is_deleted == False)
                .values(is_deleted=True)
            )
            await session.commit()
            logger.info(f"Soft-deleted {result.rowcount} verifications older than {days} days")

    asyncio.run(_cleanup())


@celery_app.task
def generate_usage_report(organization_id: str, month: str):
    """Generate monthly usage report for an organization."""
    logger.info(f"Generating usage report for org {organization_id}, month {month}")

    async def _generate():
        from sqlalchemy import select, func
        from app.core.database import async_session_factory
        from app.models.verification import Verification, VerificationStatus
        from app.models.organization import Organization

        year, month_num = map(int, month.split("-"))

        async with async_session_factory() as session:
            # Get org info
            org_result = await session.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            org = org_result.scalar_one_or_none()
            if not org:
                logger.error(f"Organization {organization_id} not found")
                return

            # Count verifications for the month
            from sqlalchemy import extract
            total = (await session.execute(
                select(func.count()).where(
                    Verification.organization_id == organization_id,
                    extract("month", Verification.created_at) == month_num,
                    extract("year", Verification.created_at) == year,
                )
            )).scalar() or 0

            completed = (await session.execute(
                select(func.count()).where(
                    Verification.organization_id == organization_id,
                    Verification.status == VerificationStatus.completed,
                    extract("month", Verification.created_at) == month_num,
                    extract("year", Verification.created_at) == year,
                )
            )).scalar() or 0

            report = {
                "organization": org.name,
                "month": month,
                "total_verifications": total,
                "completed_verifications": completed,
                "plan": org.plan.value,
                "limit": org.max_verifications_per_month,
                "usage_pct": round(total / max(org.max_verifications_per_month, 1) * 100, 1),
            }
            logger.info(f"Usage report for {org.name}: {report}")
            return report

    return asyncio.run(_generate())
