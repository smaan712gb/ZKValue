import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy import select, func, extract, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification, VerificationStatus, VerificationModule
from app.models.credit_portfolio import CreditPortfolio
from app.models.ai_asset import AIAsset
from app.models.schedule import DriftAlert, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_verification_trends(self, org_id: UUID, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly verification counts and trends."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
        result = await self.session.execute(
            select(
                extract("year", Verification.created_at).label("year"),
                extract("month", Verification.created_at).label("month"),
                func.count().label("total"),
                func.count(case((Verification.status == VerificationStatus.completed, 1))).label("completed"),
                func.count(case((Verification.status == VerificationStatus.failed, 1))).label("failed"),
            )
            .where(
                Verification.organization_id == org_id,
                Verification.is_deleted == False,
                Verification.created_at >= cutoff,
            )
            .group_by("year", "month")
            .order_by("year", "month")
        )
        rows = result.all()
        return [
            {
                "year": int(r.year),
                "month": int(r.month),
                "date": f"{int(r.year)}-{int(r.month):02d}",
                "total": r.total,
                "completed": r.completed,
                "failed": r.failed,
                "success_rate": round(r.completed / r.total * 100, 1) if r.total > 0 else 0,
            }
            for r in rows
        ]

    async def get_portfolio_performance(self, org_id: UUID) -> Dict[str, Any]:
        """Get aggregate portfolio performance metrics."""
        result = await self.session.execute(
            select(
                func.count().label("total_portfolios"),
                func.sum(CreditPortfolio.total_principal).label("total_principal"),
                func.sum(CreditPortfolio.nav_value).label("total_nav"),
                func.avg(CreditPortfolio.weighted_avg_rate).label("avg_rate"),
                func.avg(CreditPortfolio.avg_ltv_ratio).label("avg_ltv"),
                func.min(CreditPortfolio.created_at).label("first_portfolio"),
                func.max(CreditPortfolio.created_at).label("last_portfolio"),
            ).where(
                CreditPortfolio.organization_id == org_id,
                CreditPortfolio.is_deleted == False,
            )
        )
        row = result.one()
        return {
            "total_portfolios": row.total_portfolios or 0,
            "total_principal": float(row.total_principal or 0),
            "total_nav": float(row.total_nav or 0),
            "avg_rate": float(row.avg_rate or 0),
            "avg_ltv": float(row.avg_ltv or 0),
            "nav_to_principal_ratio": round(float(row.total_nav or 0) / float(row.total_principal or 1), 4),
            "first_portfolio_date": row.first_portfolio.isoformat() if row.first_portfolio else None,
            "last_portfolio_date": row.last_portfolio.isoformat() if row.last_portfolio else None,
        }

    async def get_ai_asset_performance(self, org_id: UUID) -> Dict[str, Any]:
        """Get aggregate AI asset performance metrics."""
        result = await self.session.execute(
            select(
                func.count().label("total_assets"),
                func.sum(AIAsset.estimated_value).label("total_value"),
                func.avg(AIAsset.confidence_score).label("avg_confidence"),
                func.count(case((AIAsset.ias38_compliant == True, 1))).label("ias38_compliant"),
                func.count(case((AIAsset.asc350_compliant == True, 1))).label("asc350_compliant"),
            ).where(
                AIAsset.organization_id == org_id,
                AIAsset.is_deleted == False,
            )
        )
        row = result.one()
        total = row.total_assets or 0
        return {
            "total_assets": total,
            "total_value": float(row.total_value or 0),
            "avg_confidence": float(row.avg_confidence or 0),
            "ias38_compliance_rate": round(row.ias38_compliant / max(total, 1) * 100, 1),
            "asc350_compliance_rate": round(row.asc350_compliant / max(total, 1) * 100, 1),
        }

    async def get_asset_type_breakdown(self, org_id: UUID) -> List[Dict[str, Any]]:
        """Get value breakdown by asset type."""
        result = await self.session.execute(
            select(
                AIAsset.asset_type,
                func.count().label("count"),
                func.sum(AIAsset.estimated_value).label("total_value"),
                func.avg(AIAsset.confidence_score).label("avg_confidence"),
            )
            .where(AIAsset.organization_id == org_id, AIAsset.is_deleted == False)
            .group_by(AIAsset.asset_type)
        )
        return [
            {
                "asset_type": row.asset_type.value,
                "count": row.count,
                "total_value": float(row.total_value or 0),
                "avg_confidence": float(row.avg_confidence or 0),
            }
            for row in result.all()
        ]

    async def get_alert_summary(self, org_id: UUID) -> Dict[str, Any]:
        """Get summary of drift alerts."""
        result = await self.session.execute(
            select(
                DriftAlert.severity,
                DriftAlert.status,
                func.count().label("count"),
            )
            .where(DriftAlert.organization_id == org_id, DriftAlert.is_deleted == False)
            .group_by(DriftAlert.severity, DriftAlert.status)
        )
        summary = {"total": 0, "active": 0, "by_severity": {"info": 0, "warning": 0, "critical": 0}}
        for row in result.all():
            summary["total"] += row.count
            if row.status == AlertStatus.active:
                summary["active"] += row.count
            summary["by_severity"][row.severity.value] = summary["by_severity"].get(row.severity.value, 0) + row.count
        return summary

    async def get_processing_stats(self, org_id: UUID) -> Dict[str, Any]:
        """Get verification processing time statistics."""
        result = await self.session.execute(
            select(
                Verification.module,
                func.count().label("total"),
                func.avg(
                    extract("epoch", Verification.completed_at) - extract("epoch", Verification.created_at)
                ).label("avg_duration_sec"),
            )
            .where(
                Verification.organization_id == org_id,
                Verification.status == VerificationStatus.completed,
                Verification.completed_at != None,
                Verification.is_deleted == False,
            )
            .group_by(Verification.module)
        )
        return {
            row.module.value: {
                "total_completed": row.total,
                "avg_processing_seconds": round(float(row.avg_duration_sec or 0), 1),
            }
            for row in result.all()
        }
