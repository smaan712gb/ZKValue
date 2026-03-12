from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/verification-trends")
async def get_verification_trends(
    months: int = Query(12, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    trends = await engine.get_verification_trends(user.organization_id, months)
    return {"trends": trends, "months": months}


@router.get("/portfolio-performance")
async def get_portfolio_performance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    return await engine.get_portfolio_performance(user.organization_id)


@router.get("/ai-asset-performance")
async def get_ai_asset_performance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    return await engine.get_ai_asset_performance(user.organization_id)


@router.get("/asset-type-breakdown")
async def get_asset_type_breakdown(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    breakdown = await engine.get_asset_type_breakdown(user.organization_id)
    return {"breakdown": breakdown}


@router.get("/alert-summary")
async def get_alert_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    return await engine.get_alert_summary(user.organization_id)


@router.get("/processing-stats")
async def get_processing_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    stats = await engine.get_processing_stats(user.organization_id)
    return {"stats": stats}


@router.get("/overview")
async def get_analytics_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a comprehensive analytics overview."""
    engine = AnalyticsEngine(db)
    trends = await engine.get_verification_trends(user.organization_id, 6)
    portfolio = await engine.get_portfolio_performance(user.organization_id)
    ai_assets = await engine.get_ai_asset_performance(user.organization_id)
    breakdown = await engine.get_asset_type_breakdown(user.organization_id)
    alerts = await engine.get_alert_summary(user.organization_id)
    processing = await engine.get_processing_stats(user.organization_id)

    return {
        "verification_trends": trends,
        "portfolio_performance": portfolio,
        "ai_asset_performance": ai_assets,
        "asset_type_breakdown": breakdown,
        "alert_summary": alerts,
        "processing_stats": processing,
    }
