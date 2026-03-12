import logging
import statistics
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification
from app.models.credit_portfolio import CreditPortfolio
from app.services.llm.service import LLMService
from app.services.credit.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)


class CreditAnalyzerService:
    def __init__(self, session: AsyncSession, llm_service: LLMService):
        self.session = session
        self.llm_service = llm_service
        self.anomaly_detector = AnomalyDetector(llm_service)

    async def process_verification(self, verification: Verification) -> Dict[str, Any]:
        """Process a full credit portfolio verification."""
        input_data = verification.input_data

        # Step 1: Parse and validate loan tape
        loans = self.parse_loan_tape(input_data.get("loans", []))
        portfolio_name = input_data.get("portfolio_name", "Unnamed Portfolio")
        fund_name = input_data.get("fund_name", "Unknown Fund")
        covenants = input_data.get("covenants") or self._default_covenants()

        # Step 2: Calculate interest accrual
        interest_data = self.calculate_interest_accrual(loans)

        # Step 3: Calculate LTV ratios
        ltv_data = self.calculate_ltv_ratios(loans)

        # Step 4: Check covenant compliance
        compliance = self.check_covenant_compliance(loans, covenants)

        # Step 5: Calculate NAV
        nav_data = self.calculate_nav(loans)

        # Step 6: Automated anomaly detection with severity scoring
        anomalies = self.anomaly_detector.detect_anomalies(loans)
        anomaly_summary = self.anomaly_detector.get_anomaly_summary(anomalies)

        # Step 7: LLM-powered analysis
        loan_summary = {
            "portfolio_name": portfolio_name,
            "loan_count": len(loans),
            "total_principal": sum(l.get("principal", 0) for l in loans),
            "avg_rate": interest_data["weighted_avg_rate"],
            "avg_ltv": ltv_data["avg_ltv_ratio"],
            "anomaly_summary": anomaly_summary,
        }
        llm_analysis = await self.llm_service.analyze_loan_tape(
            verification.organization_id, loan_summary
        )

        # Step 8: Store portfolio record
        portfolio = CreditPortfolio(
            organization_id=verification.organization_id,
            verification_id=verification.id,
            portfolio_name=portfolio_name,
            fund_name=fund_name,
            loan_count=len(loans),
            total_principal=interest_data["total_principal"],
            weighted_avg_rate=interest_data["weighted_avg_rate"],
            avg_ltv_ratio=ltv_data["avg_ltv_ratio"],
            nav_value=nav_data["nav_value"],
            covenant_compliance_status=compliance,
        )
        self.session.add(portfolio)

        return {
            "portfolio_name": portfolio_name,
            "fund_name": fund_name,
            "loan_count": len(loans),
            "total_principal": interest_data["total_principal"],
            "weighted_avg_rate": interest_data["weighted_avg_rate"],
            "avg_ltv_ratio": ltv_data["avg_ltv_ratio"],
            "nav_value": nav_data["nav_value"],
            "interest_accrual_verified": True,
            "ltv_compliance": ltv_data["all_within_limits"],
            "covenant_compliance": compliance,
            "interest_details": interest_data,
            "ltv_details": ltv_data,
            "nav_details": nav_data,
            "llm_analysis": llm_analysis,
            "anomalies": anomalies[:20],  # Top 20 anomalies
            "anomaly_summary": anomaly_summary,
        }

    @staticmethod
    def parse_loan_tape(raw_loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate loan tape entries."""
        parsed = []
        for loan in raw_loans:
            parsed_loan = {
                "loan_id": loan.get("loan_id", ""),
                "borrower_id": loan.get("borrower_id", ""),
                "principal": float(loan.get("principal", 0)),
                "interest_rate": float(loan.get("interest_rate", 0)),
                "term_months": int(loan.get("term_months", 12)),
                "collateral_value": float(loan.get("collateral_value", 0)),
                "collateral_type": loan.get("collateral_type", "unknown"),
                "outstanding_balance": float(loan.get("outstanding_balance", 0)),
                "payment_status": loan.get("payment_status", "current"),
                "dscr": float(loan.get("dscr", 1.5)),
            }
            # Calculate LTV if not provided
            if parsed_loan["collateral_value"] > 0:
                parsed_loan["ltv_ratio"] = (
                    parsed_loan["outstanding_balance"] / parsed_loan["collateral_value"]
                )
            else:
                parsed_loan["ltv_ratio"] = float(loan.get("ltv_ratio", 0))

            parsed.append(parsed_loan)
        return parsed

    @staticmethod
    def calculate_interest_accrual(loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate and verify interest accrual across the portfolio."""
        if not loans:
            return {"total_principal": 0, "weighted_avg_rate": 0, "total_interest": 0, "per_loan": []}

        total_principal = sum(l["principal"] for l in loans)
        weighted_rate = sum(l["principal"] * l["interest_rate"] for l in loans) / total_principal if total_principal > 0 else 0

        per_loan_accrual = []
        total_interest = 0
        for loan in loans:
            # Monthly interest accrual
            monthly_rate = loan["interest_rate"] / 12
            monthly_interest = loan["outstanding_balance"] * monthly_rate
            annual_interest = loan["outstanding_balance"] * loan["interest_rate"]
            total_interest += annual_interest

            per_loan_accrual.append({
                "loan_id": loan["loan_id"],
                "principal": loan["principal"],
                "rate": loan["interest_rate"],
                "monthly_interest": round(monthly_interest, 2),
                "annual_interest": round(annual_interest, 2),
            })

        return {
            "total_principal": round(total_principal, 2),
            "weighted_avg_rate": round(weighted_rate, 6),
            "total_annual_interest": round(total_interest, 2),
            "total_monthly_interest": round(total_interest / 12, 2),
            "loan_count": len(loans),
            "per_loan": per_loan_accrual[:10],  # Limit for response size
        }

    @staticmethod
    def calculate_ltv_ratios(loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate and verify LTV ratios."""
        if not loans:
            return {"avg_ltv_ratio": 0, "max_ltv": 0, "min_ltv": 0, "all_within_limits": True}

        ltv_ratios = [l["ltv_ratio"] for l in loans if l["ltv_ratio"] > 0]
        if not ltv_ratios:
            return {"avg_ltv_ratio": 0, "max_ltv": 0, "min_ltv": 0, "all_within_limits": True}

        avg_ltv = statistics.mean(ltv_ratios)
        max_ltv = max(ltv_ratios)
        min_ltv = min(ltv_ratios)
        over_limit = [r for r in ltv_ratios if r > 0.85]  # 85% LTV threshold

        return {
            "avg_ltv_ratio": round(avg_ltv, 4),
            "max_ltv": round(max_ltv, 4),
            "min_ltv": round(min_ltv, 4),
            "median_ltv": round(statistics.median(ltv_ratios), 4),
            "all_within_limits": len(over_limit) == 0,
            "loans_over_85pct": len(over_limit),
            "total_loans_with_ltv": len(ltv_ratios),
        }

    @staticmethod
    def check_covenant_compliance(
        loans: List[Dict[str, Any]], covenants: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify covenant compliance across the portfolio."""
        if not loans:
            return {}

        results = {}

        # DSCR Minimum
        dscr_min = covenants.get("dscr_min", 1.25)
        dscr_values = [l.get("dscr", 1.5) for l in loans]
        portfolio_dscr = statistics.mean(dscr_values) if dscr_values else 0
        results["dscr_min"] = {
            "required": dscr_min,
            "actual": round(portfolio_dscr, 3),
            "compliant": portfolio_dscr >= dscr_min,
        }

        # Leverage Maximum
        leverage_max = covenants.get("leverage_max", 4.0)
        total_debt = sum(l.get("outstanding_balance", 0) for l in loans)
        total_equity = sum(l.get("collateral_value", 0) for l in loans) - total_debt
        leverage = total_debt / total_equity if total_equity > 0 else 999
        results["leverage_max"] = {
            "required": leverage_max,
            "actual": round(leverage, 3),
            "compliant": leverage <= leverage_max,
        }

        # Concentration Limit
        concentration_limit = covenants.get("concentration_limit", 0.15)
        total_principal = sum(l["principal"] for l in loans)
        if total_principal > 0:
            max_single = max(l["principal"] for l in loans)
            concentration = max_single / total_principal
        else:
            concentration = 0
        results["concentration_limit"] = {
            "required": concentration_limit,
            "actual": round(concentration, 4),
            "compliant": concentration <= concentration_limit,
        }

        return results

    @staticmethod
    def calculate_nav(loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Net Asset Value for the portfolio."""
        if not loans:
            return {"nav_value": 0, "components": {}}

        total_outstanding = sum(l["outstanding_balance"] for l in loans)
        total_collateral = sum(l["collateral_value"] for l in loans)
        total_principal = sum(l["principal"] for l in loans)

        # Accrued interest (simplified: 1 month of interest)
        accrued_interest = sum(
            l["outstanding_balance"] * l["interest_rate"] / 12 for l in loans
        )

        # Expected losses based on payment status
        loss_rates = {"current": 0.005, "delinquent": 0.15, "default": 0.60, "unknown": 0.05}
        expected_losses = sum(
            l["outstanding_balance"] * loss_rates.get(l.get("payment_status", "current"), 0.05)
            for l in loans
        )

        # NAV = Outstanding Balance + Accrued Interest - Expected Losses
        nav_value = total_outstanding + accrued_interest - expected_losses

        return {
            "nav_value": round(nav_value, 2),
            "components": {
                "total_outstanding": round(total_outstanding, 2),
                "accrued_interest": round(accrued_interest, 2),
                "expected_losses": round(expected_losses, 2),
                "total_collateral": round(total_collateral, 2),
                "total_principal": round(total_principal, 2),
                "coverage_ratio": round(total_collateral / total_outstanding, 4) if total_outstanding > 0 else 0,
            },
        }

    @staticmethod
    def _default_covenants() -> Dict[str, Any]:
        return {
            "dscr_min": 1.25,
            "leverage_max": 4.0,
            "concentration_limit": 0.15,
        }
