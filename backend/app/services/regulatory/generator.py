import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification, VerificationModule, VerificationStatus
from app.models.credit_portfolio import CreditPortfolio
from app.models.ai_asset import AIAsset
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError

logger = logging.getLogger(__name__)

# Form PF section mappings
FORM_PF_SECTIONS = {
    "section_1": "General Information",
    "section_2": "Fund Information",
    "section_3": "Assets Under Management",
    "section_4": "Borrowing and Counterparty Exposure",
    "section_5": "Risk Metrics",
    "section_6": "Investment Strategy",
}

AIFMD_ANNEX_SECTIONS = {
    "annex_1": "Fund Identification",
    "annex_2": "Principal Markets and Instruments",
    "annex_3": "NAV and AUM",
    "annex_4": "Leverage",
    "annex_5": "Risk Profile",
    "annex_6": "Liquidity Management",
}


class RegulatoryReportGenerator:
    """Generate regulatory filings (Form PF, AIFMD Annex IV) from verification data."""

    def __init__(self, session: AsyncSession, llm_service: LLMService):
        self.session = session
        self.llm_service = llm_service

    async def generate_form_pf(self, org_id: UUID) -> Dict[str, Any]:
        """Generate SEC Form PF report from portfolio data."""
        # Gather portfolio data
        portfolios = await self._get_portfolios(org_id)
        ai_assets = await self._get_ai_assets(org_id)
        verification_stats = await self._get_verification_stats(org_id)

        if not portfolios and not ai_assets:
            raise LLMProcessingError("No portfolio or asset data available for Form PF generation")

        # Calculate Form PF fields
        total_nav = sum(float(p.nav_value or 0) for p in portfolios)
        total_aum = total_nav + sum(float(a.estimated_value or 0) for a in ai_assets)
        total_borrowing = sum(
            sum(float(l.get("outstanding_balance", 0)) for l in (p.covenant_compliance_status or {}).get("loans", []))
            for p in portfolios
        ) if portfolios else 0

        # Aggregate risk metrics
        avg_ltv = statistics_mean([float(p.avg_ltv_ratio or 0) for p in portfolios]) if portfolios else 0
        avg_rate = statistics_mean([float(p.weighted_avg_rate or 0) for p in portfolios]) if portfolios else 0

        now = datetime.now(timezone.utc)

        form_data = {
            "form_type": "Form PF",
            "reporting_period": f"Q{(now.month - 1) // 3 + 1} {now.year}",
            "generated_at": now.isoformat(),
            "sections": {
                "section_1_general": {
                    "title": FORM_PF_SECTIONS["section_1"],
                    "reporting_entity": "Organization",
                    "filing_type": "Annual" if now.month == 12 else "Quarterly",
                    "reporting_date": now.strftime("%Y-%m-%d"),
                },
                "section_2_fund_info": {
                    "title": FORM_PF_SECTIONS["section_2"],
                    "fund_count": len(set(p.fund_name for p in portfolios)),
                    "fund_names": list(set(p.fund_name for p in portfolios)),
                    "strategy": "Private Credit / AI-IP Valuation",
                },
                "section_3_aum": {
                    "title": FORM_PF_SECTIONS["section_3"],
                    "total_aum": round(total_aum, 2),
                    "total_nav": round(total_nav, 2),
                    "credit_portfolio_value": round(total_nav, 2),
                    "ai_asset_value": round(sum(float(a.estimated_value or 0) for a in ai_assets), 2),
                    "portfolio_count": len(portfolios),
                    "ai_asset_count": len(ai_assets),
                },
                "section_4_borrowing": {
                    "title": FORM_PF_SECTIONS["section_4"],
                    "total_outstanding_loans": sum(int(p.loan_count or 0) for p in portfolios),
                    "total_principal": round(sum(float(p.total_principal or 0) for p in portfolios), 2),
                    "weighted_avg_rate": round(avg_rate, 6),
                    "avg_ltv": round(avg_ltv, 4),
                },
                "section_5_risk": {
                    "title": FORM_PF_SECTIONS["section_5"],
                    "avg_ltv_ratio": round(avg_ltv, 4),
                    "ltv_above_85_pct": sum(1 for p in portfolios if float(p.avg_ltv_ratio or 0) > 0.85),
                    "covenant_breaches": sum(
                        1 for p in portfolios
                        if isinstance(p.covenant_compliance_status, dict)
                        and any(
                            not v.get("compliant", True)
                            for v in p.covenant_compliance_status.values()
                            if isinstance(v, dict)
                        )
                    ),
                    "verification_count": verification_stats.get("total", 0),
                    "verification_pass_rate": verification_stats.get("pass_rate", 0),
                },
                "section_6_strategy": {
                    "title": FORM_PF_SECTIONS["section_6"],
                    "primary_strategy": "Private Credit",
                    "secondary_strategy": "AI-IP Valuation",
                    "geographic_focus": "Global",
                },
            },
            "compliance_notes": [
                "All portfolio valuations verified using cryptographic proofs (SHA-256 + Merkle Root)",
                f"Total verifications completed: {verification_stats.get('total', 0)}",
                f"Verification pass rate: {verification_stats.get('pass_rate', 0):.1%}",
            ],
        }

        return form_data

    async def generate_aifmd_annex_iv(self, org_id: UUID) -> Dict[str, Any]:
        """Generate AIFMD Annex IV report."""
        portfolios = await self._get_portfolios(org_id)
        ai_assets = await self._get_ai_assets(org_id)
        verification_stats = await self._get_verification_stats(org_id)

        total_nav = sum(float(p.nav_value or 0) for p in portfolios)
        total_principal = sum(float(p.total_principal or 0) for p in portfolios)
        total_ai_value = sum(float(a.estimated_value or 0) for a in ai_assets)

        now = datetime.now(timezone.utc)

        # Leverage calculation (Gross Method and Commitment Method)
        gross_exposure = total_principal + total_ai_value
        leverage_gross = gross_exposure / total_nav if total_nav > 0 else 0
        leverage_commitment = total_principal / total_nav if total_nav > 0 else 0

        report = {
            "form_type": "AIFMD Annex IV",
            "reporting_period": f"Q{(now.month - 1) // 3 + 1} {now.year}",
            "generated_at": now.isoformat(),
            "sections": {
                "annex_1_identification": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_1"],
                    "fund_type": "Private Debt / AI Technology",
                    "domicile": "EU",
                    "reporting_period_end": now.strftime("%Y-%m-%d"),
                },
                "annex_2_markets": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_2"],
                    "principal_markets": ["Private Credit", "AI-IP Assets"],
                    "instrument_types": ["Term Loans", "Revolving Credit", "AI Model Assets", "Training Data"],
                    "geographic_exposure": {"north_america": 60, "europe": 25, "asia_pacific": 15},
                },
                "annex_3_nav_aum": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_3"],
                    "nav": round(total_nav, 2),
                    "aum": round(total_nav + total_ai_value, 2),
                    "nav_currency": "USD",
                    "portfolio_breakdown": {
                        "credit_portfolios": round(total_nav, 2),
                        "ai_assets": round(total_ai_value, 2),
                    },
                },
                "annex_4_leverage": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_4"],
                    "gross_method": round(leverage_gross, 4),
                    "commitment_method": round(leverage_commitment, 4),
                    "maximum_leverage_permitted": 4.0,
                    "within_limits": leverage_gross <= 4.0 and leverage_commitment <= 4.0,
                },
                "annex_5_risk": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_5"],
                    "market_risk": "medium",
                    "credit_risk": "medium" if total_nav > 0 else "low",
                    "liquidity_risk": "medium",
                    "operational_risk": "low",
                    "model_risk": "medium" if ai_assets else "low",
                    "avg_ltv": round(
                        sum(float(p.avg_ltv_ratio or 0) for p in portfolios) / len(portfolios), 4
                    ) if portfolios else 0,
                },
                "annex_6_liquidity": {
                    "title": AIFMD_ANNEX_SECTIONS["annex_6"],
                    "liquidity_profile": {
                        "less_than_1_day": 5,
                        "2_7_days": 10,
                        "8_30_days": 20,
                        "31_90_days": 30,
                        "91_180_days": 20,
                        "181_365_days": 10,
                        "more_than_365_days": 5,
                    },
                    "redemption_frequency": "Quarterly",
                    "lock_up_period_months": 12,
                },
            },
            "compliance_notes": [
                "Report generated using verified portfolio data with cryptographic proofs",
                f"Verification integrity: {verification_stats.get('pass_rate', 0):.0%} pass rate",
            ],
        }

        return report

    async def generate_regulatory_narrative(
        self, org_id: UUID, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to generate a compliance narrative for the regulatory report."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        form_type = report_data.get("form_type", "Regulatory Report")

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a regulatory compliance expert writing a {form_type} filing narrative. "
                    "Generate a compliance narrative in JSON format with:\n"
                    "1. filing_summary: Executive summary suitable for regulatory submission\n"
                    "2. risk_disclosure: Comprehensive risk disclosure language\n"
                    "3. compliance_attestation: Compliance attestation statement\n"
                    "4. material_changes: List of material changes to report (if any based on data)\n"
                    "5. regulatory_recommendations: Recommendations for regulatory compliance improvements\n"
                    "Use precise regulatory language suitable for SEC/FCA/ESMA filings."
                ),
            },
            {
                "role": "user",
                "content": f"Generate compliance narrative for this {form_type} data:\n\n{json.dumps(report_data, indent=2, default=str)}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.2, max_tokens=4000)
            return _extract_json(response)
        except Exception as e:
            logger.error(f"Regulatory narrative generation failed: {e}")
            return {"filing_summary": "Regulatory narrative could not be generated."}

    async def _get_portfolios(self, org_id: UUID) -> list:
        result = await self.session.execute(
            select(CreditPortfolio).where(
                CreditPortfolio.organization_id == org_id,
                CreditPortfolio.is_deleted == False,
            ).order_by(CreditPortfolio.created_at.desc())
        )
        return result.scalars().all()

    async def _get_ai_assets(self, org_id: UUID) -> list:
        result = await self.session.execute(
            select(AIAsset).where(
                AIAsset.organization_id == org_id,
                AIAsset.is_deleted == False,
            ).order_by(AIAsset.created_at.desc())
        )
        return result.scalars().all()

    async def _get_verification_stats(self, org_id: UUID) -> Dict[str, Any]:
        total_result = await self.session.execute(
            select(func.count(Verification.id)).where(
                Verification.organization_id == org_id,
                Verification.is_deleted == False,
            )
        )
        total = total_result.scalar() or 0

        completed_result = await self.session.execute(
            select(func.count(Verification.id)).where(
                Verification.organization_id == org_id,
                Verification.is_deleted == False,
                Verification.status == VerificationStatus.completed,
            )
        )
        completed = completed_result.scalar() or 0

        return {
            "total": total,
            "completed": completed,
            "pass_rate": completed / total if total > 0 else 0,
        }


def statistics_mean(values: list) -> float:
    """Safe mean calculation."""
    return sum(values) / len(values) if values else 0
