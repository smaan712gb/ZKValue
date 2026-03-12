import logging
import statistics
from typing import Dict, Any, List
from uuid import UUID
from app.services.llm.service import LLMService, LLMProcessingError

logger = logging.getLogger(__name__)


class AnomalySeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyDetector:
    """Automated loan tape anomaly detection with severity scoring."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def detect_anomalies(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run all anomaly detection checks on a loan tape."""
        if not loans:
            return []

        anomalies = []
        anomalies.extend(self._check_duplicate_borrowers(loans))
        anomalies.extend(self._check_rate_outliers(loans))
        anomalies.extend(self._check_ltv_breaches(loans))
        anomalies.extend(self._check_concentration_risk(loans))
        anomalies.extend(self._check_stale_collateral(loans))
        anomalies.extend(self._check_payment_status_issues(loans))
        anomalies.extend(self._check_dscr_violations(loans))

        # Sort by severity
        severity_order = {AnomalySeverity.CRITICAL: 0, AnomalySeverity.HIGH: 1, AnomalySeverity.MEDIUM: 2, AnomalySeverity.LOW: 3}
        anomalies.sort(key=lambda a: severity_order.get(a["severity"], 99))

        return anomalies

    def get_anomaly_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of detected anomalies."""
        by_severity = {}
        for a in anomalies:
            sev = a["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        risk_score = (
            by_severity.get(AnomalySeverity.CRITICAL, 0) * 25
            + by_severity.get(AnomalySeverity.HIGH, 0) * 15
            + by_severity.get(AnomalySeverity.MEDIUM, 0) * 5
            + by_severity.get(AnomalySeverity.LOW, 0) * 1
        )

        if risk_score >= 50:
            overall = "critical"
        elif risk_score >= 25:
            overall = "high"
        elif risk_score >= 10:
            overall = "medium"
        else:
            overall = "low"

        return {
            "total_anomalies": len(anomalies),
            "by_severity": by_severity,
            "risk_score": min(risk_score, 100),
            "overall_risk": overall,
        }

    def _check_duplicate_borrowers(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect duplicate borrower IDs which may indicate data issues."""
        anomalies = []
        borrower_counts: Dict[str, int] = {}
        for loan in loans:
            bid = loan.get("borrower_id", "")
            if bid:
                borrower_counts[bid] = borrower_counts.get(bid, 0) + 1

        for bid, count in borrower_counts.items():
            if count > 3:
                anomalies.append({
                    "type": "duplicate_borrower",
                    "severity": AnomalySeverity.HIGH,
                    "message": f"Borrower '{bid}' appears {count} times — possible concentration or data duplication",
                    "details": {"borrower_id": bid, "count": count},
                    "recommendation": "Verify if these are distinct loans or data errors",
                })
        return anomalies

    def _check_rate_outliers(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect interest rates that are statistical outliers."""
        anomalies = []
        rates = [l.get("interest_rate", 0) for l in loans if l.get("interest_rate", 0) > 0]
        if len(rates) < 3:
            return anomalies

        mean_rate = statistics.mean(rates)
        stdev = statistics.stdev(rates) if len(rates) > 1 else 0

        for loan in loans:
            rate = loan.get("interest_rate", 0)
            if rate > 0 and stdev > 0:
                z_score = abs(rate - mean_rate) / stdev
                if z_score > 3:
                    anomalies.append({
                        "type": "rate_outlier",
                        "severity": AnomalySeverity.MEDIUM,
                        "message": f"Loan '{loan.get('loan_id')}' rate {rate:.4f} is {z_score:.1f} std devs from mean ({mean_rate:.4f})",
                        "details": {"loan_id": loan.get("loan_id"), "rate": rate, "mean": mean_rate, "z_score": round(z_score, 2)},
                        "recommendation": "Verify rate is correct and not a data entry error",
                    })
        return anomalies

    def _check_ltv_breaches(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect loans with dangerous LTV ratios."""
        anomalies = []
        for loan in loans:
            ltv = loan.get("ltv_ratio", 0)
            if ltv > 1.0:
                anomalies.append({
                    "type": "ltv_underwater",
                    "severity": AnomalySeverity.CRITICAL,
                    "message": f"Loan '{loan.get('loan_id')}' is underwater with LTV {ltv:.2%}",
                    "details": {"loan_id": loan.get("loan_id"), "ltv": ltv, "balance": loan.get("outstanding_balance"), "collateral": loan.get("collateral_value")},
                    "recommendation": "Immediate review required — loan balance exceeds collateral value",
                })
            elif ltv > 0.90:
                anomalies.append({
                    "type": "ltv_warning",
                    "severity": AnomalySeverity.HIGH,
                    "message": f"Loan '{loan.get('loan_id')}' has high LTV of {ltv:.2%}",
                    "details": {"loan_id": loan.get("loan_id"), "ltv": ltv},
                    "recommendation": "Monitor closely — approaching underwater territory",
                })
        return anomalies

    def _check_concentration_risk(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for excessive portfolio concentration."""
        anomalies = []
        total_principal = sum(l.get("principal", 0) for l in loans)
        if total_principal <= 0:
            return anomalies

        # Check by collateral type
        by_type: Dict[str, float] = {}
        for loan in loans:
            ct = loan.get("collateral_type", "unknown")
            by_type[ct] = by_type.get(ct, 0) + loan.get("principal", 0)

        for ctype, amount in by_type.items():
            pct = amount / total_principal
            if pct > 0.40:
                anomalies.append({
                    "type": "concentration_risk",
                    "severity": AnomalySeverity.HIGH if pct > 0.60 else AnomalySeverity.MEDIUM,
                    "message": f"Collateral type '{ctype}' represents {pct:.1%} of portfolio — concentration risk",
                    "details": {"collateral_type": ctype, "percentage": round(pct * 100, 1), "amount": amount},
                    "recommendation": "Consider diversifying collateral exposure",
                })

        # Check single borrower concentration
        by_borrower: Dict[str, float] = {}
        for loan in loans:
            bid = loan.get("borrower_id", "unknown")
            by_borrower[bid] = by_borrower.get(bid, 0) + loan.get("principal", 0)

        for bid, amount in by_borrower.items():
            pct = amount / total_principal
            if pct > 0.15:
                anomalies.append({
                    "type": "borrower_concentration",
                    "severity": AnomalySeverity.HIGH if pct > 0.25 else AnomalySeverity.MEDIUM,
                    "message": f"Borrower '{bid}' represents {pct:.1%} of total principal — single-name concentration",
                    "details": {"borrower_id": bid, "percentage": round(pct * 100, 1), "amount": amount},
                    "recommendation": "Review single-borrower exposure limits",
                })
        return anomalies

    def _check_stale_collateral(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect loans with suspiciously low or zero collateral values."""
        anomalies = []
        for loan in loans:
            collateral = loan.get("collateral_value", 0)
            balance = loan.get("outstanding_balance", 0)
            if balance > 0 and collateral == 0:
                anomalies.append({
                    "type": "missing_collateral",
                    "severity": AnomalySeverity.CRITICAL,
                    "message": f"Loan '{loan.get('loan_id')}' has outstanding balance ${balance:,.0f} but zero collateral value",
                    "details": {"loan_id": loan.get("loan_id"), "balance": balance},
                    "recommendation": "Update collateral valuation or flag as unsecured",
                })
        return anomalies

    def _check_payment_status_issues(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for high default/delinquency rates."""
        anomalies = []
        total = len(loans)
        if total == 0:
            return anomalies

        status_counts: Dict[str, int] = {}
        for loan in loans:
            status = loan.get("payment_status", "current")
            status_counts[status] = status_counts.get(status, 0) + 1

        default_count = status_counts.get("default", 0)
        delinquent_count = status_counts.get("delinquent", 0)
        problem_pct = (default_count + delinquent_count) / total

        if problem_pct > 0.15:
            anomalies.append({
                "type": "high_default_rate",
                "severity": AnomalySeverity.CRITICAL,
                "message": f"Portfolio has {problem_pct:.1%} problem loans ({default_count} defaults, {delinquent_count} delinquent)",
                "details": {"default_count": default_count, "delinquent_count": delinquent_count, "total": total},
                "recommendation": "Immediate portfolio review and loss provisioning assessment required",
            })
        elif problem_pct > 0.05:
            anomalies.append({
                "type": "elevated_default_rate",
                "severity": AnomalySeverity.HIGH,
                "message": f"Portfolio has elevated problem loan rate of {problem_pct:.1%}",
                "details": {"default_count": default_count, "delinquent_count": delinquent_count, "total": total},
                "recommendation": "Monitor deteriorating credits and adjust loss reserves",
            })
        return anomalies

    def _check_dscr_violations(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for loans below minimum DSCR thresholds."""
        anomalies = []
        for loan in loans:
            dscr = loan.get("dscr", 1.5)
            if dscr < 1.0:
                anomalies.append({
                    "type": "dscr_critical",
                    "severity": AnomalySeverity.CRITICAL,
                    "message": f"Loan '{loan.get('loan_id')}' has DSCR {dscr:.2f} — borrower cannot cover debt service",
                    "details": {"loan_id": loan.get("loan_id"), "dscr": dscr},
                    "recommendation": "Immediate restructuring discussion recommended",
                })
            elif dscr < 1.25:
                anomalies.append({
                    "type": "dscr_warning",
                    "severity": AnomalySeverity.MEDIUM,
                    "message": f"Loan '{loan.get('loan_id')}' has DSCR {dscr:.2f} — below covenant minimum of 1.25x",
                    "details": {"loan_id": loan.get("loan_id"), "dscr": dscr},
                    "recommendation": "Monitor borrower cash flows closely",
                })
        return anomalies

    async def generate_anomaly_narrative(
        self, org_id: UUID, anomalies: List[Dict[str, Any]], portfolio_summary: Dict[str, Any]
    ) -> str:
        """Use LLM to generate a human-readable anomaly narrative."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a credit risk analyst writing an anomaly report for a private credit portfolio. "
                    "Summarize the detected anomalies in clear, actionable language for the fund manager. "
                    "Prioritize the most severe issues. Keep it under 500 words."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Portfolio: {json.dumps(portfolio_summary, default=str)}\n\n"
                    f"Detected anomalies:\n{json.dumps(anomalies[:20], default=str)}"
                ),
            },
        ]

        import json
        try:
            return await provider.chat(messages, model=model, temperature=0.4, max_tokens=1000)
        except Exception as e:
            logger.error(f"Anomaly narrative generation failed: {e}")
            return "Anomaly narrative could not be generated."
