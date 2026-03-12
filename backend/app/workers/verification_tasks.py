import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _make_session_factory():
    """Create a fresh async engine + session factory for each task invocation.

    This avoids the 'Future attached to a different loop' error that occurs
    when Celery tasks call asyncio.run() — each run() creates a new event
    loop, but a module-level engine/pool is bound to the old one.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_verification_task(self, verification_id: str):
    """Process a verification asynchronously via Celery."""
    logger.info(f"Processing verification {verification_id}")
    try:
        from app.services.verification.engine import VerificationEngine

        async def _process():
            session_factory, engine = _make_session_factory()
            try:
                async with session_factory() as session:
                    ve = VerificationEngine(session)
                    await ve.process_verification(verification_id)
            finally:
                await engine.dispose()

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
        from app.services.verification.proof import ProofService

        async def _generate():
            session_factory, engine = _make_session_factory()
            try:
                async with session_factory() as session:
                    proof_service = ProofService(session)
                    await proof_service.generate_and_store_certificate(verification_id)
            finally:
                await engine.dispose()

        asyncio.run(_generate())
        logger.info(f"Report for {verification_id} generated successfully")
    except Exception as exc:
        logger.error(f"Report generation for {verification_id} failed: {exc}")
        raise self.retry(exc=exc)
