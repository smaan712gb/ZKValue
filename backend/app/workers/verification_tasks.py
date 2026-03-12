import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_verification_task(self, verification_id: str):
    """Process a verification asynchronously via Celery."""
    logger.info(f"Processing verification {verification_id}")
    try:
        from app.core.database import async_session_factory
        from app.services.verification.engine import VerificationEngine

        async def _process():
            async with async_session_factory() as session:
                engine = VerificationEngine(session)
                await engine.process_verification(verification_id)

        asyncio.run(_process())
        logger.info(f"Verification {verification_id} completed successfully")
    except Exception as exc:
        logger.error(f"Verification {verification_id} failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def generate_report_task(self, verification_id: str, report_type: str = "pdf"):
    """Generate a report for a completed verification."""
    logger.info(f"Generating {report_type} report for verification {verification_id}")
    try:
        from app.core.database import async_session_factory
        from app.services.verification.proof import ProofService

        async def _generate():
            async with async_session_factory() as session:
                proof_service = ProofService(session)
                await proof_service.generate_and_store_certificate(verification_id)

        asyncio.run(_generate())
        logger.info(f"Report for {verification_id} generated successfully")
    except Exception as exc:
        logger.error(f"Report generation for {verification_id} failed: {exc}")
        raise self.retry(exc=exc)
