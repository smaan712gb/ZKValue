import asyncio
import logging
from app.workers.celery_app import celery_app
from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.blockchain_tasks.daily_blockchain_anchor")
def daily_blockchain_anchor():
    """Create a daily blockchain anchor of all verification proofs."""
    asyncio.run(_anchor())


async def _anchor():
    async with async_session_factory() as session:
        from app.services.blockchain.anchor import BlockchainAnchorService

        service = BlockchainAnchorService(session)
        result = await service.create_daily_anchor()
        await session.commit()
        logger.info(f"Daily blockchain anchor: {result}")
        return result
