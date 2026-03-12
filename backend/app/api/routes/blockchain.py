from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.blockchain.anchor import BlockchainAnchorService

router = APIRouter(prefix="/blockchain", tags=["Blockchain Anchoring"])


@router.post("/anchor")
async def create_anchor(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a blockchain anchor for today's verification proofs."""
    if user.role.value not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owners and admins can create blockchain anchors")

    service = BlockchainAnchorService(db)
    result = await service.create_daily_anchor()
    await db.commit()
    return result


@router.get("/anchors")
async def list_anchors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all blockchain anchors."""
    service = BlockchainAnchorService(db)
    return await service.get_anchors(page, page_size)


@router.get("/verify/{proof_hash}")
async def verify_on_chain(
    proof_hash: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify that a specific proof hash is anchored on-chain."""
    service = BlockchainAnchorService(db)
    return await service.verify_proof_on_chain(proof_hash)
