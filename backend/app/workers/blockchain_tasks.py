import asyncio
import logging
from app.workers.celery_app import celery_app
from app.workers.verification_tasks import _make_session_factory

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.blockchain_tasks.daily_blockchain_anchor")
def daily_blockchain_anchor():
    """Create a daily blockchain anchor of all verification proofs."""

    async def _anchor():
        from app.services.blockchain.anchor import BlockchainAnchorService

        session_factory, engine = _make_session_factory()
        try:
            async with session_factory() as session:
                service = BlockchainAnchorService(session)
                result = await service.create_daily_anchor()
                await session.commit()
                logger.info(f"Daily blockchain anchor: {result}")
                return result
        finally:
            await engine.dispose()

    asyncio.run(_anchor())
