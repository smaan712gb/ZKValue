import logging
import random
import statistics
from typing import Dict, Any, List
from uuid import UUID
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError
import json

logger = logging.getLogger(__name__)


# Macroeconomic scenario presets
SCENARIO_PRESETS = {
    "base_case": {
        "name": "Base Case",
        "rate_shock_bps": 0,
        "default_multiplier": 1.0,
        "collateral_haircut": 0.0,
        "gdp_growth": 0.025,
        "unemployment_delta": 0.0,
        "description": "Current economic conditions continue unchanged",
    },
    "mild_recession": {
        "name": "Mild Recession",
        "rate_shock_bps": 100,
        "default_multiplier": 1.5,
        "collateral_haircut": 0.10,
        "gdp_growth": -0.01,
        "unemployment_delta": 0.02,
        "description": "Moderate economic downturn with rising rates",
    },
    "severe_recession": {
        "name": "Severe Recession",
        "rate_shock_bps": 200,
        "default_multiplier": 3.0,
        "collateral_haircut": 0.25,
        "gdp_growth": -0.04,
        "unemployment_delta": 0.05,
        "description": "Deep recession similar to 2008-2009",
    },
    "stagflation": {
        "name": "Stagflation",
        "rate_shock_bps": 400,
        "default_multiplier": 2.0,
        "collateral_haircut": 0.15,
        "gdp_growth": -0.005,
        "unemployment_delta": 0.03,
        "description": "High inflation with stagnant growth and aggressive rate hikes",
    },
    "rate_spike": {
        "name": "Rate Spike",
        "rate_shock_bps": 300,
        "default_multiplier": 1.3,
        "collateral_haircut": 0.05,
        "gdp_growth": 0.01,
        "unemployment_delta": 0.01,
        "description": "Sudden interest rate spike with limited economic impact",
    },
    "credit_crisis": {
        "name": "Credit Crisis",
        "rate_shock_bps": 50,
        "default_multiplier": 4.0,
        "collateral_haircut": 0.30,
        "gdp_growth": -0.03,
        "unemployment_delta": 0.04,
        "description": "Systemic credit event with widespread defaults and collateral collapse",
    },
}


class StressTestEngine:
    """Monte Carlo stress testing for private credit portfolios."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def run_scenario(
        self, loans: List[Dict[str, Any]], scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single deterministic stress scenario on a portfolio."""
        rate_shock = scenario.get("rate_shock_bps", 0) / 10000  # Convert bps to decimal
        default_mult = scenario.get("default_multiplier", 1.0)
        collateral_haircut = scenario.get("collateral_haircut", 0.0)

        stressed_loans = []
        total_losses = 0.0
        total_outstanding = 0.0

        for loan in loans:
            balance = float(loan.get("outstanding_balance", loan.get("principal", 0)))
            rate = float(loan.get("interest_rate", 0))
            collateral = float(loan.get("collateral_value", 0))
            dscr = float(loan.get("dscr", 1.5))
            status = loan.get("payment_status", "current")

            # Stress the rate
            stressed_rate = rate + rate_shock

            # Stress collateral
            stressed_collateral = collateral * (1 - collateral_haircut)

            # Stressed LTV
            stressed_ltv = balance / stressed_collateral if stressed_collateral > 0 else 999

            # Stressed DSCR (higher rates reduce coverage)
            rate_impact = (1 + rate_shock / max(rate, 0.01)) if rate > 0 else 1
            stressed_dscr = dscr / rate_impact

            # Default probability based on stressed metrics
            base_pd = {"current": 0.02, "delinquent": 0.15, "default": 1.0}.get(status, 0.05)
            stressed_pd = min(base_pd * default_mult, 1.0)

            # Increase PD for underwater/low-DSCR loans
            if stressed_ltv > 1.0:
                stressed_pd = min(stressed_pd * 1.5, 1.0)
            if stressed_dscr < 1.0:
                stressed_pd = min(stressed_pd * 2.0, 1.0)

            # Loss given default
            lgd = max(1 - (stressed_collateral / balance), 0.0) if balance > 0 else 0.4
            lgd = min(lgd + 0.1, 1.0)  # Add recovery costs

            expected_loss = balance * stressed_pd * lgd
            total_losses += expected_loss
            total_outstanding += balance

            stressed_loans.append({
                "loan_id": loan.get("loan_id", ""),
                "original_balance": balance,
                "stressed_rate": round(stressed_rate, 6),
                "stressed_ltv": round(stressed_ltv, 4),
                "stressed_dscr": round(stressed_dscr, 3),
                "default_probability": round(stressed_pd, 4),
                "loss_given_default": round(lgd, 4),
                "expected_loss": round(expected_loss, 2),
            })

        # Portfolio-level stressed metrics
        stressed_nav = total_outstanding - total_losses
        loss_rate = total_losses / total_outstanding if total_outstanding > 0 else 0

        return {
            "scenario_name": scenario.get("name", "Custom"),
            "scenario_description": scenario.get("description", ""),
            "parameters": {
                "rate_shock_bps": scenario.get("rate_shock_bps", 0),
                "default_multiplier": scenario.get("default_multiplier", 1.0),
                "collateral_haircut_pct": scenario.get("collateral_haircut", 0) * 100,
            },
            "results": {
                "total_outstanding": round(total_outstanding, 2),
                "total_expected_losses": round(total_losses, 2),
                "loss_rate": round(loss_rate, 4),
                "stressed_nav": round(stressed_nav, 2),
                "nav_impact_pct": round(loss_rate * 100, 2),
                "loans_underwater": sum(1 for l in stressed_loans if l["stressed_ltv"] > 1.0),
                "loans_dscr_below_1": sum(1 for l in stressed_loans if l["stressed_dscr"] < 1.0),
                "avg_stressed_ltv": round(
                    statistics.mean([l["stressed_ltv"] for l in stressed_loans]) if stressed_loans else 0, 4
                ),
                "avg_default_probability": round(
                    statistics.mean([l["default_probability"] for l in stressed_loans]) if stressed_loans else 0, 4
                ),
            },
            "loan_details": stressed_loans[:20],  # Top 20 for response size
        }

    def run_monte_carlo(
        self,
        loans: List[Dict[str, Any]],
        num_simulations: int = 1000,
        seed: int | None = None,
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation with random parameter sampling."""
        if seed is not None:
            random.seed(seed)

        # Cap simulations
        num_simulations = min(num_simulations, 10000)

        total_outstanding = sum(
            float(l.get("outstanding_balance", l.get("principal", 0))) for l in loans
        )

        simulation_losses = []
        simulation_navs = []

        for _ in range(num_simulations):
            # Sample random macro parameters
            rate_shock_bps = random.gauss(50, 150)  # Mean 50bps, std 150bps
            default_mult = max(0.5, random.lognormvariate(0, 0.5))  # Log-normal
            collateral_haircut = max(0, min(0.5, random.gauss(0.05, 0.10)))

            scenario = {
                "rate_shock_bps": rate_shock_bps,
                "default_multiplier": default_mult,
                "collateral_haircut": collateral_haircut,
            }

            result = self.run_scenario(loans, scenario)
            simulation_losses.append(result["results"]["total_expected_losses"])
            simulation_navs.append(result["results"]["stressed_nav"])

        # Calculate distribution statistics
        simulation_losses.sort()
        simulation_navs.sort()

        def percentile(data: List[float], pct: float) -> float:
            idx = int(len(data) * pct / 100)
            return data[min(idx, len(data) - 1)]

        return {
            "num_simulations": num_simulations,
            "total_outstanding": round(total_outstanding, 2),
            "loss_distribution": {
                "mean": round(statistics.mean(simulation_losses), 2),
                "median": round(statistics.median(simulation_losses), 2),
                "std_dev": round(statistics.stdev(simulation_losses), 2) if len(simulation_losses) > 1 else 0,
                "percentile_5": round(percentile(simulation_losses, 5), 2),
                "percentile_25": round(percentile(simulation_losses, 25), 2),
                "percentile_75": round(percentile(simulation_losses, 75), 2),
                "percentile_95": round(percentile(simulation_losses, 95), 2),
                "percentile_99": round(percentile(simulation_losses, 99), 2),
                "max": round(max(simulation_losses), 2),
                "min": round(min(simulation_losses), 2),
            },
            "nav_distribution": {
                "mean": round(statistics.mean(simulation_navs), 2),
                "median": round(statistics.median(simulation_navs), 2),
                "percentile_5": round(percentile(simulation_navs, 5), 2),
                "percentile_95": round(percentile(simulation_navs, 95), 2),
                "worst_case": round(min(simulation_navs), 2),
                "best_case": round(max(simulation_navs), 2),
            },
            "risk_metrics": {
                "expected_loss_rate": round(statistics.mean(simulation_losses) / total_outstanding * 100, 2) if total_outstanding > 0 else 0,
                "var_95": round(percentile(simulation_losses, 95), 2),
                "var_99": round(percentile(simulation_losses, 99), 2),
                "cvar_95": round(
                    statistics.mean(simulation_losses[int(len(simulation_losses) * 0.95):]) if simulation_losses else 0, 2
                ),
            },
        }

    def run_all_presets(self, loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all predefined stress scenarios."""
        results = {}
        for key, scenario in SCENARIO_PRESETS.items():
            results[key] = self.run_scenario(loans, scenario)
        return {
            "scenarios": results,
            "scenario_count": len(results),
            "loan_count": len(loans),
        }

    async def generate_stress_narrative(
        self, org_id: UUID, stress_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to generate a narrative analysis of stress test results."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior risk analyst writing a stress test report for a private credit fund's risk committee. "
                    "Analyze the stress test results and provide a JSON report with:\n"
                    "1. executive_summary: 2-paragraph overview of portfolio resilience\n"
                    "2. scenario_commentary: analysis of each scenario's impact\n"
                    "3. key_vulnerabilities: list of portfolio weaknesses exposed by stress tests\n"
                    "4. risk_rating: overall portfolio stress resilience (strong/adequate/weak/critical)\n"
                    "5. recommendations: actionable risk mitigation recommendations\n"
                    "Use professional language suitable for LP reporting and risk committee presentations."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze these stress test results:\n\n{json.dumps(stress_results, indent=2, default=str)}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3, max_tokens=4000)
            return _extract_json(response)
        except Exception as e:
            logger.error(f"Stress narrative generation failed: {e}")
            return {"executive_summary": "Stress test narrative could not be generated."}
